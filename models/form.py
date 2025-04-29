from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()], default=datetime.today)
    time = TimeField('Time', validators=[DataRequired()], default=datetime.now)
    location = StringField('Location', validators=[DataRequired()])
    submit = SubmitField('Create Event')