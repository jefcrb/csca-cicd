from . import db

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jaar = db.Column(db.String(6))
    maand = db.Column(db.String(3))
    handelsnaam = db.Column(db.String(255))
    productnaam = db.Column(db.String(255))
    segment = db.Column(db.String(255))
    energietype = db.Column(db.String(255))
    contracttype = db.Column(db.String(255))
    vast_variabel_dynamisch = db.Column(db.String(255))
    prijsonderdeel = db.Column(db.String(255))
    indexatieparameter_x = db.Column(db.String(255))
    indexatieparameter_y = db.Column(db.String(255))
    beschrijving_x = db.Column(db.Text)
    beschrijving_y = db.Column(db.Text)
    waarde_x_vreg = db.Column(db.Float)
    waarde_y_vreg = db.Column(db.Float)
    waarde_x_laatst_gekende = db.Column(db.Float)
    waarde_y_laatst_gekende = db.Column(db.Float)
    a = db.Column(db.Float)
    b = db.Column(db.Float)
    c = db.Column(db.Float)
    d = db.Column(db.Float)
    prijs = db.Column(db.Float)
    wkk = db.Column(db.Float)
    groene_stroom = db.Column(db.Float)
    vaste_vergoeding = db.Column(db.Float)
    vaste_vergoeding_enkelvoudige_meter = db.Column(db.Float)
    vaste_vergoeding_tweevoudige_meter = db.Column(db.Float)
    vaste_vergoeding_uitsluitend_nachttarief = db.Column(db.Float)

    __table_args__ = (
        db.UniqueConstraint('jaar', 'maand', 'handelsnaam', 'productnaam', 'prijsonderdeel', name='_data_uc'),
    )

    def to_dict(self):
        return {
            'jaar': self.jaar,
            'maand': self.maand,
            'handelsnaam': self.handelsnaam,
            'productnaam': self.productnaam,
            'segment': self.segment,
            'energietype': self.energietype,
            'contracttype': self.contracttype,
            'vast_variabel_dynamisch': self.vast_variabel_dynamisch,
            'prijsonderdeel': self.prijsonderdeel,
            'indexatieparameter_x': self.indexatieparameter_x,
            'indexatieparameter_y': self.indexatieparameter_y,
            'beschrijving_x': self.beschrijving_x,
            'beschrijving_y': self.beschrijving_y,
            'waarde_x_vreg': self.waarde_x_vreg,
            'waarde_y_vreg': self.waarde_y_vreg,
            'waarde_x_laatst_gekende': self.waarde_x_laatst_gekende,
            'waarde_y_laatst_gekende': self.waarde_y_laatst_gekende,
            'a': self.a,
            'b': self.b,
            'c': self.c,
            'd': self.d,
            'prijs': self.prijs,
            'wkk': self.wkk,
            'groene_stroom': self.groene_stroom,
            'vaste_vergoeding': self.vaste_vergoeding,
            'vaste_vergoeding_enkelvoudige_meter': self.vaste_vergoeding_enkelvoudige_meter,
            'vaste_vergoeding_tweevoudige_meter': self.vaste_vergoeding_tweevoudige_meter,
            'vaste_vergoeding_uitsluitend_nachttarief': self.vaste_vergoeding_uitsluitend_nachttarief
        }
