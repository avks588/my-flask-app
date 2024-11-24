import sys
print(sys.executable)
from flask import Flask, request, redirect, url_for, flash, session, Response, render_template
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session handling

# In-memory storage for user data (replace with a database in production)
users = {}

# Home Route (Redirects to login if not logged in)
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('screener'))
    return redirect(url_for('login'))

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('screener'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if username in users:
            flash('Username already exists.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            users[username] = password
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template("sign_up.html")

# Stock Screener Route
@app.route('/screener', methods=['GET', 'POST'])
def screener():
    if 'user' not in session:
        flash('Please log in to access the stock screener.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        action = request.form.get('action')

        # Stock Screener functionality
        if action == 'screener' and uploaded_file and uploaded_file.filename != '':
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
            try:
                ranked_data = run_stock_screener(file_path)
                flash('Stock screening completed successfully!', 'success')
                return Response(
                    f"""
                    <html>
                        <head>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    margin: 20px;
                                }}
                                table {{
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin-top: 20px;
                                }}
                                table, th, td {{
                                    border: 1px solid #ddd;
                                }}
                                th {{
                                    background-color: #007BFF;
                                    color: white;
                                    padding: 10px;
                                }}
                                td {{
                                    padding: 8px;
                                    text-align: center;
                                }}
                                tr:nth-child(even) {{
                                    background-color: #f2f2f2;
                                }}
                                tr:hover {{
                                    background-color: #ddd;
                                }}
                            </style>
                        </head>
                        <body>
                            <center><h1>Stock Screening Results</h1></center>
                            {ranked_data.to_html(classes='data', header='true')}
                        </body>
                    </html>
                    """, mimetype="text/html"
                )
            except Exception as e:
                flash(f"Error processing file: {e}", 'error')

        # Stock Investigator functionality
        '''elif action == 'investigator' and uploaded_file and uploaded_file.filename != '':
            file_path = os.path.join("uploads", uploaded_file.filename)
            uploaded_file.save(file_path)
            try:
                investigator_data = run_stock_investigator(file_path)
                flash('Stock investigation completed successfully!', 'success')
                return render_template('screener.html', investigator_data=investigator_data.to_html(classes='table table-bordered table-striped', header='true'), action="investigator")
            except Exception as e:
                flash(f"Error processing file: {e}", 'error')'''

    return render_template('screener.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Stock Screener Logic (same as your previous script)
def run_stock_screener(file_path):
    # Load the CSV file
    data = pd.read_csv(file_path)

    # Process numeric columns
    numeric_columns = [
        'operating_profit_sep_2021',
        'operating_profit_sep_2022',
        'eps_sep_2021',
        'eps_sep_2022',
        'promoter_holding_sep_2021',
        'promoter_holding_sep_2022'
    ]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Fill missing values
    data = data.fillna(0)

    # Compute growth metrics
    data['eps_growth'] = (data['eps_sep_2022'] - data['eps_sep_2021']) / data['eps_sep_2021'].abs()
    data['operating_profit_growth'] = (
        (data['operating_profit_sep_2022'] - data['operating_profit_sep_2021'])
        / data['operating_profit_sep_2021'].abs()
    )
    data['promoter_holding_normalized'] = data['promoter_holding_sep_2022']

    # Define scoring system
    weights = {
        'eps_growth': 0.4,
        'operating_profit_growth': 0.4,
        'promoter_holding_normalized': 0.2
    }
    data['total_score'] = (
        weights['eps_growth'] * data['eps_growth'] +
        weights['operating_profit_growth'] * data['operating_profit_growth'] +
        weights['promoter_holding_normalized'] * data['promoter_holding_normalized']
    )

    # Rank stocks
    data['rank'] = data['total_score'].rank(ascending=False)
    ranked_data = data.sort_values(by='rank').reset_index(drop=True)
    return ranked_data[['stock_symbol', 'total_score', 'rank']]

def run_stock_investigator(file_path):
    print(f"Processing file: {file_path}")
    pass

if __name__ == '__main__':
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)
