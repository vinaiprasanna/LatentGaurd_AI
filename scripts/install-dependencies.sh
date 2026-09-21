cd frontend
npm install
cd ..
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
cd ..
cd model-training
pip install -r requirements.txt
cd ..
deactivate
