from app import db


class Currency(db.Model):
    __tablename__ = 'currency'
    id = db.Column(db.Integer, primary_key=True, supports_dict=True)
    name = db.Column(db.String(3), unique=True, nullable=False, supports_dict=True)

    rates = db.relationship("Rate", cascade='all,delete', passive_deletes=True, backref="currency",
                            lazy=True)

    def __repr__(self):
        return '<Currency %d %r>' % (self.id, self.name)


class Rate(db.Model):
    __tablename__ = 'rate'

    id = db.Column(db.Integer, primary_key=True, supports_dict=True)

    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id', ondelete='CASCADE'),
                            nullable=False, supports_dict=True)

    date = db.Column(db.Date, nullable=False, supports_dict=True)
    rate = db.Column(db.Float, nullable=False, supports_dict=True)
    volume = db.Column(db.Float, nullable=False, supports_dict=True)

    def __repr__(self):
        return '<Rate %s>' % str({k: v for (k, v) in self.__dict__.items()
                                  if not k.startswith('_')})


db.Index('currency_date', Rate.currency_id, Rate.date)
