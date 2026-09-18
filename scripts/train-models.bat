.venv\Scripts\activate
cd model-training
python anomaly_ensemble/train.py
python drift_model/train.py
cd ..
