import functools
import io

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.security import (check_password_hash, generate_password_hash)
from sqlalchemy import select

from beergame.db import db_session,Supervisor 




bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = db_session.execute(select(Supervisor).where(Supervisor.id == user_id)).scalars().first()

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view

@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form.get("username", '').strip()
        password = request.form.get("password", '').strip()
        confirm_password = request.form.get("confirm_password", '').strip()
        error = ''
        if username == '':
            error += "Un nom d'utilisateur est requis."
            flash(error)

        if password == '':
            error += "Un mot de passe est requis."
            flash(error)

        if confirm_password == '':
            error += "Une confirmation du mot de passe est requise."
            flash(error)
        if password != confirm_password:
            error += "Les deux mots de passe ne sont pas identiques."
            flash(error)
        preexistant_user = db_session.execute(
            select(Supervisor).
            where(Supervisor.username == username)
        ).scalars().first()
        if preexistant_user is not None:
            error += f"Le nom d'utilisateur {username} est déjà utilisé. "
            flash(error)

        if error == '':
            # the name is available, store it in the database and go to
            # the login page
            new_user = Supervisor(
                username=username,
                password=generate_password_hash(password)
                #client_demand=2,
                #administrator = True
            )

            db_session.add(new_user)
            db_session.commit()
            flash("Votre compte a été créé.")
            return redirect(url_for("auth.login"))


    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered supervisor by adding the supervisor id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        
        user = db_session.execute(select(Supervisor).where(Supervisor.username == username)).scalars().first()
        
        if user is None:
            error = "Le nom d'utilisateur n'est pas valide."
            flash(error)
        elif not check_password_hash(user.password, password):
            error = "Le mot de passe n'est pas valide."
            flash(error)

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")

@login_required
@bp.route('/logout', methods=("GET",))
def logout():
    session.clear()
    return redirect(url_for('index'))
