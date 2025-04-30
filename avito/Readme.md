# Avito Data Processing and Analysis

This repository contains scripts and notebooks for processing and analyzing data related to Avito. The main entry point for running the data processing pipeline is the `final_pipeline.ipynb` Jupyter notebook.

## Setup Instructions

To get started, follow these steps to set up your environment and run the pipeline:

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://gitlab.atp-fivt.org/it-purple-hack/team176/avito.git
cd avito
```

### 2. Set Up a Virtual Environment

It is recommended to use a virtual environment to manage dependencies. You can create one using `venv`:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python packages using `pip` and the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Run the Jupyter Notebook

Ensure you have Jupyter installed, then start the Jupyter Notebook server:

```bash
jupyter notebook
```

Open the `final_pipeline.ipynb` notebook in your browser and run the cells to execute the data processing pipeline.

## Project Structure

- `requirements.txt`: Contains the list of Python packages required to run the project.
- `final_pipeline.ipynb`: The main Jupyter notebook for running the data processing and analysis pipeline.
