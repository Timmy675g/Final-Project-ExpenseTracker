from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_required, current_user
from db import db, User, Entry
from loginregister import auth_bp, bcrypt
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production') #Encrypts data so hackers cant easily use things like "id=10"

os.makedirs('instance', exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money.db' #Now this is SQLite or the Storage basically
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_balance_warning(balance):
    """Return warning message based on balance level"""
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

def calculate_balance(user_id):
    """Calculate total balance for a user"""
    entries = Entry.query.filter_by(user_id=user_id).all()
    return sum(e.amount for e in entries)

@app.route("/", methods=["GET"])
@login_required
def home():
    """Main dashboard showing all entries and balance"""
    try:
        entries = Entry.query.filter_by(user_id=current_user.id).order_by(Entry.id.desc()).all()
        balance = calculate_balance(current_user.id)
        warning = get_balance_warning(balance)
        
        return render_template(
            "index.html", 
            entries=entries, 
            Balance=balance, 
            warning=warning
        )
    except Exception as e:
        flash('An error occurred while loading your entries.', 'error')
        return render_template("index.html", entries=[], Balance=0, warning=None)

@app.route("/moneh-enter", methods=["POST"])
@login_required
def submit():
    """Add new income or expense entry"""
    try:
        #Form data
        amount_str = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()
        entry_type = request.form.get('type', 'income')
        category = request.form.get('category', '').strip()

        #Validating amount
        if not amount_str:
            flash('Please enter an amount.', 'warning')
            return redirect(url_for('home'))

        try:
            amount = float(amount_str)
            if amount <= 0:
                flash('Amount must be greater than zero.', 'warning')
                return redirect(url_for('home'))
        except ValueError:
            flash('Invalid amount. Please enter a valid number.', 'error')
            return redirect(url_for('home'))

        # Convert to negative for expenses
        if entry_type == 'expense':
            amount = -abs(amount)

        # Create entry with description or category
        entry = Entry(
            amount=amount,
            description=description if description else category,
            type=entry_type,
            category=category,
            user_id=current_user.id
        )

        db.session.add(entry)
        db.session.commit()
        
        flash(f'Successfully added {entry_type}!', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while saving your entry.', 'error')
        return redirect(url_for('home'))

@app.route("/delete/<int:entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    """Delete a specific entry"""
    try:
        entry = Entry.query.filter_by(id=entry_id, user_id=current_user.id).first()
        
        if not entry:
            flash('Entry not found or you do not have permission to delete it.', 'error')
            return redirect(url_for('home'))

        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the entry.', 'error')
    
    return redirect(url_for('home'))

@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    """Edit an existing entry"""
    entry = Entry.query.filter_by(id=entry_id, user_id=current_user.id).first()
    
    if not entry:
        flash('Entry not found.', 'error')
        return redirect(url_for('home'))
    
    if request.method == "POST":
        try:
            amount_str = request.form.get('amount', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            
            if amount_str:
                try:
                    amount = float(amount_str)
                    if entry.type == 'expense':
                        amount = -abs(amount)
                    entry.amount = amount
                except ValueError:
                    flash('Invalid amount.', 'error')
                    return redirect(url_for('edit_entry', entry_id=entry_id))
            
            entry.description = description if description else category
            entry.category = category
            
            db.session.commit()
            flash('Entry updated successfully!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the entry.', 'error')
    
    return render_template('edit.html', entry=entry)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

app.register_blueprint(auth_bp)

if __name__ == "__main__":
    print("Starting Flask Money Tracker...")
    with app.app_context():
        db.create_all()
    
    app.run()