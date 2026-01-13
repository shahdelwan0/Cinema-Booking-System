from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database
db = SQLAlchemy()


# User Model
class Users(db.Model):
    __tablename__ = "Users"

    UserID = db.Column(db.Integer, primary_key=True)
    UserName = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(255), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    PhoneNumber = db.Column(db.String(20))
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    is_active = True
    is_authenticated = True
    is_anonymous = False

    def get_id(self):
        return str(self.UserID)

    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)


class Movies(db.Model):
    __tablename__ = "Movies"

    MovieID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    DurationMinutes = db.Column(db.Integer, nullable=False)
    Rating = db.Column(
        db.Numeric(3, 2), CheckConstraint("Rating BETWEEN 0 AND 10"), nullable=False
    )  # Rating constraint
    ReleaseDate = db.Column(db.Date)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    TicketPrice = db.Column(db.Numeric(10, 2), nullable=False)
    PosterURL = db.Column(db.String(500))


# Screen Model
class Screens(db.Model):
    __tablename__ = "Screens"

    ScreenID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    TotalSeats = db.Column(
        db.Integer, CheckConstraint("TotalSeats > 0"), nullable=False
    )  # TotalSeats constraint
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


# Seat Model
class Seats(db.Model):
    __tablename__ = "Seats"

    SeatID = db.Column(db.Integer, primary_key=True)
    ScreenID = db.Column(db.Integer, db.ForeignKey("Screens.ScreenID"), nullable=False)
    SeatNumber = db.Column(db.String(10), nullable=False)
    RowNumber = db.Column(db.String(5))
    Status = db.Column(
        db.String(20), default="Available"
    )  # Options: 'Available', 'Locked', 'Booked'
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    screen = db.relationship("Screens", backref=db.backref("seats", lazy=True))


class Schedules(db.Model):
    __tablename__ = "Schedules"

    ScheduleID = db.Column(db.Integer, primary_key=True)
    MovieID = db.Column(db.Integer, db.ForeignKey("Movies.MovieID"), nullable=False)
    ScreenID = db.Column(db.Integer, db.ForeignKey("Screens.ScreenID"), nullable=False)
    ShowTime = db.Column(db.DateTime, nullable=False)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    # Relationship with Movies
    movie = db.relationship("Movies", backref=db.backref("schedules", lazy=True))
    # Relationship with Screens
    screen = db.relationship("Screens", backref=db.backref("schedules", lazy=True))


# Booking Model
class Bookings(db.Model):
    __tablename__ = "Bookings"

    BookingID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    ScheduleID = db.Column(
        db.Integer, db.ForeignKey("Schedules.ScheduleID"), nullable=False
    )
    BookingTime = db.Column(db.DateTime, default=db.func.current_timestamp())
    BookingStatus = db.Column(
        db.String(50), default="Pending"
    )  # Options: 'Pending', 'Confirmed', 'Cancelled'
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    TicketsBooked = db.Column(db.Integer)  # Ensure this column is here

    user = db.relationship("Users", backref=db.backref("bookings", lazy=True))
    schedule = db.relationship("Schedules", backref=db.backref("bookings", lazy=True))


# BookingDetails Model
class BookingDetails(db.Model):
    __tablename__ = "BookingDetails"

    BookingDetailID = db.Column(db.Integer, primary_key=True)
    BookingID = db.Column(
        db.Integer, db.ForeignKey("Bookings.BookingID"), nullable=False
    )
    SeatID = db.Column(db.Integer, db.ForeignKey("Seats.SeatID"), nullable=False)
    Price = db.Column(db.Numeric(10, 2), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    booking = db.relationship(
        "Bookings", backref=db.backref("booking_details", lazy=True)
    )
    seat = db.relationship("Seats", backref=db.backref("booking_details", lazy=True))
    __table_args__ = (
        UniqueConstraint("SeatID", "BookingID", name="unique_seat_booking"),
    )


# Payments Model
class Payments(db.Model):
    __tablename__ = "Payments"

    PaymentID = db.Column(db.Integer, primary_key=True)
    BookingID = db.Column(
        db.Integer, db.ForeignKey("Bookings.BookingID"), unique=True, nullable=False
    )
    PaymentMethod = db.Column(db.String(50), nullable=False)
    PaymentStatus = db.Column(db.String(50), nullable=False)
    PaymentDate = db.Column(db.DateTime, default=db.func.current_timestamp())
    CreatedAt = db.Column(db.DateTime, default=db.func.current_timestamp())
    UpdatedAt = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    booking = db.relationship("Bookings", backref=db.backref("payment", uselist=False))


# AuditLogs Model
class AuditLogs(db.Model):
    __tablename__ = "AuditLogs"

    LogID = db.Column(db.Integer, primary_key=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Users.UserID"), nullable=False)
    Action = db.Column(db.String(255), nullable=False)
    Timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship("Users", backref=db.backref("audit_logs", lazy=True))
