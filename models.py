from datetime import datetime, timezone
import math
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Voice(db.Model):
    __tablename__ = 'voices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    engine = db.Column(db.String(50))
    description = db.Column(db.String(255))
    rating = db.Column(db.Float, default=1000.0)
    matches = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)

    @property
    def win_rate(self):
        if self.matches > 0:
            return (self.wins / self.matches) * 100.0
        return 0.0

    @property
    def confidence_interval(self):
        if self.matches > 0:
            return 400.0 / math.sqrt(self.matches)
        return 400.0

    @property
    def lower_bound(self):
        return self.rating - self.confidence_interval

    @property
    def upper_bound(self):
        return self.rating + self.confidence_interval

    @property
    def reliability(self):
        MIN_MATCHES_RELIABILITY = 10.0
        if self.matches > 0:
            return min(100.0, (self.matches / MIN_MATCHES_RELIABILITY) * 100.0)
        return 0.0

    def __repr__(self):
        return f'<Voice {self.name}: {self.rating}>'

class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    voice_a_name = db.Column(db.String(100), nullable=False)
    voice_b_name = db.Column(db.String(100), nullable=False)
    chosen_voice_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<TestResult {self.voice_a_name} vs {self.voice_b_name} -> {self.chosen_voice_name}>'
