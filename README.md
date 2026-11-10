# Piyush Spare Parts Assistant

## Simple setup

1. Open the project folder in VS Code.
2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install packages:

```powershell
pip install -r requirements.txt
python -m ipykernel install --user --name spare-parts --display-name "Python (Spare Parts)"
```

4. Put your Groq key in `.env`:

```env
GROQ_API_KEY=your_real_key_here
```

5. Open `notebooks\spare_parts_assistant.ipynb`.
6. Run each numbered cell in order.

## Direct command tests

```powershell
python test_agent.py
python agent.py "Pump making grinding noise near seal"
```

## Run the complete project from one command

To run Groq, fault parsing, RAG, all six agent questions, and automated tests through one entry point:

```powershell
python run_project.py 6
```

To choose an individual stage interactively:

```powershell
python run_project.py
```

The launcher menu provides these options:

1. Test Groq
2. Run fault parser
3. Run maintenance RAG
4. Run the six agent demonstrations
5. Run automated tests
6. Run the complete project
