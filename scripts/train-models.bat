@echo off
call .venv\Scripts\activate
echo Activated virtual environment.
cd model-training
echo Initiating model training...
python anomaly_ensemble/train.py
python drift_model/train.py
cd ..
deactivate
echo Model training completed.
