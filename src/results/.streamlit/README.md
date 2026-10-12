# Customer Voice Dashboard

## Project

The Customer Voice Dashboard analyzes public customer reviews of the Moniepoint Personal Banking app.
The main business question is:

> What is our biggest customer problem right now?

## App

Moniepoint Personal Banking
Google Play package:
com.moniepoint.personal

## Technology

- Python
- Google Colab
- Google Play reviews
- Pandas
- Scikit-learn
- Gemini
- Pydantic
- Plotly
- Streamlit

## Sentiment Classes

- Positive
- Neutral
- Negative

## Complaint Categories

- Billing
- Technical
- Account Access
- Delivery
- Other

## Dashboard Features

The dashboard includes:

1. Total feedback
2. Positive percentage
3. Negative percentage
4. Neutral percentage
5. Average rating
6. Total complaints
7. Biggest customer problem
8. Sentiment distribution
9. Biggest complaint categories
10. Sentiment over time
11. Real customer reviews
12. Review search
13. Date filter
14. Sentiment filter
15. Category filter
16. Star-rating filter
17. Evaluation metrics
18. Confusion matrix
19. Real classification errors
20. Live Gemini review classification
21. Offline saved-results mode

## Evaluation

A 100-review hand-labelled test set is used as the ground truth.
Evaluation includes:

- Accuracy
- Precision
- Recall
- F1
- Macro-F1
- Confusion matrix
- Real error examples

## Project Structure

```text
customer_voice_dashboard/
■Customer Voice Dashboard — VS Code Complete Setup Page 19
■■■ app.py
■■■ requirements.txt
■■■ README.md
■■■ .gitignore
■
■■■ data/
■ ■■■ moniepoint_customer_voice_results.csv
■
■■■ results/
■ ■■■ evaluation_metrics.json
■ ■■■ gemini_sentiment_confusion_matrix.csv
■ ■■■ gemini_sentiment_errors.csv
■
■■■ src/
■ ■■■ __init__.py
■ ■■■ data_utils.py
■ ■■■ gemini_classifier.py
■
■■■ .streamlit/
■■■ secrets.toml
```

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the Dashboard

Run:

```bash
streamlit run app.py
```

The dashboard will open in the browser.

## Offline Mode

The dashboard is designed to continue working from saved CSV and evaluation files without requiring Gemini.
The live Gemini classification feature requires an internet connection and a valid Gemini API key.

## Important

Do not commit the Gemini API key to GitHub.
The key should remain inside:

```text
.streamlit/secrets.toml
```

and that file is excluded by `.gitignore`.

## Project Limitation

The current build uses Gemini as the selected sentiment classification method.
The original project brief requires comparison of at least two approaches on the same hand-labelled test set. If the team adds another approach
