from flask import Flask, render_template, request, redirect

app = Flask(__name__)

entries = []
entry_id_counter = 0

def get_balance_warning(balance):
    """Returns warning message and type based on balance"""
    if balance < 0:
        return {
            'message': '⚠️ You are in debt! Avoid any spending until you recover.',
            'type': 'danger'
        }
    elif balance <= 10:
        return {
            'message': '⚠️ Critical! Your balance is very low. Avoid spending too much!',
            'type': 'critical'
        }
    elif balance <= 20:
        return {
            'message': '⚠️ Warning! Your balance is getting low. Consider decreasing your spending.',
            'type': 'warning'
        }
    return None

@app.route("/", methods=["GET"])
def home():
    Balance = sum(entry['amount'] for entry in entries) if entries else 0
    warning = get_balance_warning(Balance)
    return render_template("index.html", 
                         entries=entries, 
                         Balance=Balance, 
                         error=None, 
                         warning=warning)

@app.route("/moneh-enter", methods=["POST"])
def submit():
    global entry_id_counter
    
    amount_str = request.form.get('amount', '').strip()
    description = request.form.get('description', '').strip()
    entry_type = request.form.get('type', 'income')
    category = request.form.get('category', '')
    
    if not amount_str:
        Balance = sum(entry['amount'] for entry in entries) if entries else 0
        warning = get_balance_warning(Balance)
        error = "Please enter an amount!"
        return render_template("index.html", 
                             entries=entries, 
                             Balance=Balance, 
                             error=error, 
                             warning=warning)
    
    try:
        amount = int(amount_str)
        if entry_type == 'expense':
            amount = -abs(amount)
        else:
            amount = abs(amount)
        
        entry = {
            'id': entry_id_counter,
            'amount': amount,
            'description': description if description else category,
            'type': entry_type,
            'category': category
        }
        
        entries.append(entry)
        entry_id_counter += 1
        return redirect("/")
    except ValueError:
        Balance = sum(entry['amount'] for entry in entries) if entries else 0
        warning = get_balance_warning(Balance)
        error = "Please enter a valid whole number only!"
        return render_template("index.html", 
                             entries=entries, 
                             Balance=Balance, 
                             error=error, 
                             warning=warning)

@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry(entry_id):
    global entries
    entries = [entry for entry in entries if entry['id'] != entry_id]
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)