cd frontend
npm install
cd ..
python -m venv .venv
.venv\Scripts\activate
cd backend
pip install -r requirements.txt
cd ..
cd model-training
pip install -r requirements.txt
cd ..
deactivate
