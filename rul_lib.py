"""Fonctions communes RUL (utilisées par le notebook et les scripts d'expérience)."""
import os

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
import numpy as np
import pandas as pd

FEATS = ['RMS', 'Energy', 'Entropy', 'Kurtosis']
WINDOW = 30

# Trajectoires jusqu'à la panne (run-to-failure) du dataset IMS
FAILURES = {
    'test2_B1': ('test2', 1),   # bague extérieure
    'test1_B3': ('test1', 3),   # bague intérieure
    'test1_B4': ('test1', 4),   # élément roulant
    'test3_B3': ('test3', 3),   # bague extérieure
}


def load_features(test, cache_dir='cache'):
    return pd.read_csv(os.path.join(cache_dir, f'features_{test}.csv'), parse_dates=['Date'])


def failure_trajectory(test, bearing, cache_dir='cache'):
    """Série temporelle d'un roulement défaillant, avec la RUL réelle en jours.
    Les acquisitions plates (capteur arrêté, RMS < 0.01) sont retirées."""
    d = load_features(test, cache_dir)
    b = d[d.Bearing == bearing].sort_values('Date').reset_index(drop=True)
    b = b[b.RMS >= 0.01].reset_index(drop=True)
    b['RUL'] = (b.Date.max() - b.Date).dt.total_seconds() / 86400
    return b


def degradation_onset(b, feat='RMS', n_base=200, z=3, consec=5):
    """Premier instant où `feat` sort durablement de la bande saine (moyenne ± z·σ
    calculée sur les `n_base` premières acquisitions)."""
    base = b[feat].iloc[:n_base]
    out = ((b[feat] - base.mean()).abs() > z * base.std()).astype(int)
    hit = out.rolling(consec).sum() >= consec
    return int(hit.idxmax() - consec + 1) if hit.any() else len(b) - 1


N_BASE = 200  # acquisitions considérées comme saines en début de vie (≈ 33 h à 10 min)


def healthy_reference(b, n_base=N_BASE):
    """Valeurs de référence du roulement neuf (médiane du début de vie)."""
    return b[FEATS].iloc[:n_base].median().to_numpy()


def relative_features(X, ref):
    """Features exprimées par rapport au roulement neuf : 1 = état sain.
    Le kurtosis (Fisher, ~0 si sain) est pris en version Pearson (+3) pour rester positif."""
    X = np.asarray(X, dtype=float).copy()
    ref = np.asarray(ref, dtype=float).copy()
    k = FEATS.index('Kurtosis')
    X[..., k] += 3; ref[k] += 3
    return X / ref


def piecewise_rul(rul, cap):
    """RUL linéaire par morceaux : plafonnée à `cap` jours tant que le roulement est sain."""
    return np.minimum(rul, cap)


def sliding_windows(X, y, w=WINDOW):
    """Fenêtre i = acquisitions [i, i+w) ; cible = RUL à la dernière acquisition de la fenêtre."""
    Xs = np.stack([X[i:i + w] for i in range(len(X) - w + 1)])
    ys = y[w - 1:]
    return Xs.astype(np.float32), ys.astype(np.float32)


def build_cnn_lstm(n_feat=len(FEATS), w=WINDOW, seed=42):
    """Même architecture que l'interface HTML (inférence JS) :
    Conv1D(128,5)-BN-Pool-Conv1D(64,3)-BN-Pool-LSTM(64)-Dense(32)-Dense(1)."""
    import keras
    from keras import layers
    keras.utils.set_random_seed(seed)
    m = keras.Sequential([
        keras.Input((w, n_feat)),
        layers.Conv1D(128, 5, activation='relu', padding='same'), layers.BatchNormalization(),
        layers.MaxPooling1D(2),
        layers.Conv1D(64, 3, activation='relu', padding='same'), layers.BatchNormalization(),
        layers.MaxPooling1D(2),
        layers.LSTM(64), layers.Dropout(0.3),
        layers.Dense(32, activation='relu'), layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss='mse', metrics=['mae'])
    return m


def build_lstm(n_feat=len(FEATS), w=WINDOW, seed=42):
    import keras
    from keras import layers
    keras.utils.set_random_seed(seed)
    m = keras.Sequential([
        keras.Input((w, n_feat)),
        layers.LSTM(64, return_sequences=True), layers.Dropout(0.2),
        layers.LSTM(32), layers.Dense(16, activation='relu'), layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss='mse', metrics=['mae'])
    return m


def fit_keras(model, Xtr, ytr, Xval, yval, epochs=150, patience=15, verbose=0):
    import keras
    cb = [keras.callbacks.EarlyStopping(monitor='val_loss', patience=patience,
                                        restore_best_weights=True)]
    return model.fit(Xtr, ytr, validation_data=(Xval, yval), epochs=epochs,
                     batch_size=32, callbacks=cb, verbose=verbose)


def metrics(y, yp):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    return {'R2': r2_score(y, yp), 'MAE': mean_absolute_error(y, yp),
            'RMSE': float(np.sqrt(mean_squared_error(y, yp)))}
