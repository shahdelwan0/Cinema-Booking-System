from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from models import Movies, db, Users, Schedules, Seats, Bookings, BookingDetails

# Initialize Flask app
app = Flask(__name__)

# Set the secret key for session management
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cinema.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with Flask app
db.init_app(app)  # This is crucial: associating SQLAlchemy with the app
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect to login if not authenticated


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Route for homepage (home page with options for login/signup)
@app.route("/")
def index():
    movies = Movies.query.all()
    return render_template("index.html", movies=movies)


# Route for user signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Get the user details from the form
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Check if email already exists
        existing_user = Users.query.filter_by(Email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        # Create new user
        new_user = Users(UserName=username, Email=email, PasswordHash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch the user by email
        user = Users.query.filter_by(Email=email).first()

        if user and bcrypt.check_password_hash(user.PasswordHash, password):
            # Successful login
            login_user(user)  # Log the user in using Flask-Login
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))  # Redirect to dashboard or homepage
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


# Route for dashboard (after login, view all available movies)
@app.route("/dashboard")
@login_required
def dashboard():
    movies = Movies.query.all()
    return render_template("movies.html", movies=movies)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/book_now/<int:schedule_id>", methods=["GET", "POST"])
@login_required
def book_now(schedule_id):
    schedule = Schedules.query.get_or_404(schedule_id)  # Get the schedule details
    movie = Movies.query.get_or_404(schedule.MovieID)  # Get the movie details

    total_price=0
    if request.method == "POST":
        # Get the number of seats from the form
        seats = int(request.form["seats"])
        # Calculate the total price (seats * price per seat)
        total_price = (
            seats * movie.TicketPrice
        )  # Use movie.TicketPrice instead of schedule.Price

        # Create a new booking and store the number of seats (TicketsBooked)
        new_booking = Bookings(
            UserID=current_user.UserID,  # Get the current logged-in user's ID
            ScheduleID=schedule.ScheduleID,
            BookingStatus="Confirmed",
            TicketsBooked=seats,
        )

        # Add the booking to the session and commit to the database
        db.session.add(new_booking)
        db.session.commit()

        flash("Booking successful!", "success")

        # Redirect to a page showing the booking confirmation or user's bookings
        return redirect(url_for("view_bookings"))

    return render_template(
        "book_ticket.html", schedule=schedule, movie=movie, total_price=total_price
    )


@app.route("/view_bookings")
@login_required
def view_bookings():
    # Get the bookings for the current user
    bookings = Bookings.query.filter_by(UserID=current_user.UserID).all()
    for booking in bookings:
        # Assuming there's a relation from Bookings to Movies, and you can access Movie object from Booking
        movie = Movies.query.get(
            booking.schedule.MovieID
        )  # Adjust this to your actual relationship

        # Check if both TicketsBooked and TicketPrice are not None
        if booking.TicketsBooked is not None and movie.TicketPrice is not None:
            booking.total_price = booking.TicketsBooked * movie.TicketPrice
        else:
            booking.total_price = 0  # Default value if any of the values is None

    # Prepare the data to send to the template
    return render_template("view_bookings.html", bookings=bookings)


@app.route("/booking_confirmation/<int:booking_id>", methods=["GET", "POST"])
@login_required
def booking_confirmation(booking_id):
    booking = Bookings.query.get_or_404(booking_id)

    # Make sure the booking belongs to the current user
    if booking.UserID != current_user.UserID:
        flash("You do not have permission to access this booking.", "danger")
        return redirect(url_for("view_bookings"))

    movie = Movies.query.get(booking.schedule.MovieID)  # Get the related movie

    if request.method == "POST":
        if "edit" in request.form:
            # Handle editing the booking
            status = request.form.get("status")
            tickets_booked = int(request.form.get("ticketsBooked"))

            # Calculate the total price dynamically
            total_price = tickets_booked * movie.TicketPrice

            # Update the booking details
            booking.TicketsBooked = tickets_booked
            booking.BookingStatus = status
            db.session.commit()

            flash("Booking updated successfully!", "success")
            return redirect(url_for("booking_confirmation", booking_id=booking.BookingID))

        elif "delete" in request.form:
            # Handle deleting the booking
            db.session.delete(booking)
            db.session.commit()

            flash("Booking deleted successfully!", "success")
            return redirect(url_for("view_bookings"))

    return render_template("booking_confirmation.html", booking=booking, movie=movie)


@app.route("/delete_booking/<int:booking_id>", methods=["GET", "POST"])
@login_required  # If you need to restrict access to logged-in users
def delete_booking(booking_id):
    # Assuming you have a method to delete the booking by its ID
    booking = Bookings.query.get_or_404(booking_id)  # or whatever logic you're using
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted successfully!", "success")
    return redirect(url_for("view_bookings"))


# Run the app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
