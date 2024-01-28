"""
Commands for testing:

rm .\migrations\; flask db init; flask db migrate; flask db upgrade; $env:POSTGRES_HOST='localhost'; $env:POSTGRES_USER='postgres'; $env:POSTGRES_PASSWORD='a'; $env:POSTGRES_DB='app_db'; $env:SECRET_KEY='38ee1bfef77c029614cc87c3ac922f2de08f44cd75ed6e41f31477f831a1cef4'
python
from app import app; app.app_context().push(); from flaskapp.extensions import *; from flaskapp.models import *; session = db.session; import os


This module defines a set of SQLAlchemy database models representing an insurance analysis system.

The models include:
- Analysis: Represents a reinsurance analysis.
- Layer: Represents a layer within an analysis.
- HistoLossFile: Represents historical loss data files associated with an analysis.
- HistoLoss: Represents individual historical loss records.
- PremiumFile: Represents premium data files (not used for SL pricing).
- Premium: Represents individual premium records (not used for SL pricing).
- RiskProfileFile: Represents risk profile data files (not used for SL pricing).
- RiskProfile: Represents individual risk profiles (not used for SL pricing).
- ModelFile: Represents a loss model associated with an analysis.
- ModelYearLoss: Represents individual year loss records.
- ResultFile: Represents analysis results.
- PricingRelationship: Represents pricing relationships between layers and model files in results.
- ResultYearLoss: Represents individual year loss records in analysis results.

These models are designed to work with SQLAlchemy and are used to interact with the underlying database.

Relationships between the models:
- 1-to-many relationship between Analysis and Layer: done
- 1-to-many relationship between Analysis and HistoLossFile: done
- 1-to-many relationship between Analysis and PremiumFile: done
- 1-to-many relationship between Analysis and RiskProfileFile: done
- 1-to-many relationship between Analysis and ModelFile: done
- 1-to-many relationship between Analysis and PricingRelationship: done
- 1-to-many relationship between Analysis and ResultFile: done

- 1-to-many relationship between HistoLossFile and HistoLoss: done
- 1-to-many relationship between PremiumFile and Premium: done
- 1-to-many relationship between RiskProfileFile and RiskProfile: done
- 1-to-many relationship between ModelFile and ModelYearLoss: done

- 1-to-many relationship between PricingRelationship and ResultFile: done
- 1-to-many relationship between PricingRelationship and LayerToModelfile: done

- many-to-many relationship between Layer and ModelFile in the association object LayerToModelfile: done

- 1-to-many relationhip between ResultFile and ResultYearLoss: done
- 1-to-many relationship between LayerToModelfile and ResultYearLoss: done


Resources:
- Duplicate records: https://stackoverflow.com/questions/44061006/sqlalchemy-how-to-copy-deep-copy-a-entry-and-all-its-foreign-relation
- Reference: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many
- https://stackoverflow.com/questions/30406808/flask-sqlalchemy-difference-between-association-model-and-association-table-fo
- https://copyprogramming.com/howto/sqlalchemy-relationship-on-many-to-many-association-table
- https://stackoverflow.com/questions/68322485/conflicts-with-relationship-between-tables
- https://docs.sqlalchemy.org/en/14/orm/backref.html
- Cascading delete: https://www.geeksforgeeks.org/sqlalchemy-cascading-deletes/
- Cascading delete 2: https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete

"""

from flaskapp.extensions import db
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import validates, relationship, backref

# Define the constants
ANALYSIS_TABLE = 'analysis'
LAYER_TABLE = 'layer'


class Analysis(db.Model):
    __tablename__ = ANALYSIS_TABLE
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    quote = Column(Integer, nullable=False)
    client = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and Layer, HistoLossFile, PremiumFile, RiskProfileFile, ModelFile, PricingRelationship, ResultFile
    layers = relationship(LAYER_TABLE.capitalize(), back_populates='analysis', cascade='all, delete-orphan')
    histolossfiles = relationship('HistoLossFile', back_populates='analysis', cascade='all, delete-orphan')
    premiumfiles = relationship('PremiumFile', back_populates='analysis', cascade='all, delete-orphan')
    riskprofilefiles = relationship('RiskProfileFile', back_populates='analysis', cascade='all, delete-orphan')
    modelfiles = relationship('ModelFile', back_populates='analysis', cascade='all, delete-orphan')
    pricingrelationships = relationship('PricingRelationship', back_populates='analysis', cascade='all, delete-orphan')
    resultfiles = relationship('ResultFile', back_populates='analysis', cascade='all, delete-orphan')

    # https://docs.sqlalchemy.org/en/20/orm/mapped_attributes.html#simple-validators
    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The analysis name must be entered')
        return value

    @validates('quote')
    def validate_quote(self, key, value):
        if value is None or not value:
            raise ValueError('The quote number must be entered')
        if not str(value).isdigit():
            raise ValueError('The quote number must be an integer')
        return value

    @validates('client')
    def validate_client(self, key, value):
        if value is None or not value:
            raise ValueError('The client must be entered')
        return value

    def copy(self):
        new = Analysis()
        new.name = self.name + ' - Copy'
        for attr in ['quote', 'client']:
            setattr(new, attr, getattr(self, attr))
        new.layers.extend([layer.copy() for layer in self.layers])
        new.histolossfiles.extend([histolossfile.copy() for histolossfile in self.histolossfiles])
        new.premiumfiles.extend([premiumfile.copy() for premiumfile in self.premiumfiles])
        new.riskprofilefiles.extend([riskprofilefile.copy() for riskprofilefile in self.riskprofilefiles])
        new.modelfiles.extend([modelfile.copy() for modelfile in self.modelfiles])
        return new

    def __repr__(self):
        return f'<Analysis {self.id} {self.name}>'


class Layer(db.Model):
    __tablename__ = LAYER_TABLE
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    premium = Column(Integer, nullable=False)
    deductible = Column(Integer, nullable=False)
    limit = Column(Integer, nullable=False)
    display_order = Column(Integer)

    # Define the 1-to-many relationship between Analysis and Layer
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='layers')

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The layer name must be entered')
        return value

    @validates('premium', 'deductible', 'limit')
    def validate_int_col(self, key, value):
        if value is None:
            raise ValueError('The premiums, deductibles and limits must be entered for all layers')
        if not str(value).isdigit():
            raise ValueError('The premiums, deductibles and limits must all be integers')
        return value

    def copy(self):
        new = Layer()
        for attr in ['name', 'premium', 'deductible', 'limit', 'display_order']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<Layer {self.id} {self.name}>'


class HistoLossFile(db.Model):
    __tablename__ = 'histolossfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    vintage = Column(Integer, nullable=False)

    # Define the 1-to-many relationship between Analysis and HistoLossFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='histolossfiles')

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    losses = relationship('HistoLoss', back_populates='lossfile', cascade='all, delete')

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The loss file name must be entered')
        return value

    @validates('vintage')
    def validate_vintage(self, key, value):
        if value is None:
            raise ValueError('The vintage must be entered')
        if not str(value).isdigit():
            raise ValueError('The vintage must be an integer')
        return value

    def copy(self):
        new = HistoLossFile()
        for attr in ['name', 'vintage']:
            setattr(new, attr, getattr(self, attr))
        new.losses.extend([loss.copy() for loss in self.losses])
        return new

    def __repr__(self):
        return f'<HistoLossFile {self.id} {self.name}>'


class HistoLoss(db.Model):
    __tablename__ = 'histoloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    year = Column(Integer, nullable=False)
    premium = Column(Integer)
    loss = Column(Integer)
    loss_ratio = Column(Float)

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    lossfile_id = Column(Integer, ForeignKey(HistoLossFile.id))
    lossfile = relationship('HistoLossFile', back_populates='losses')

    def copy(self):
        new = HistoLoss()
        for attr in ['name', 'year', 'premium', 'loss', 'loss_ratio']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<HistoLoss {self.id} {self.name}>'


class PremiumFile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'premiumfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and PremiumFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='premiumfiles')

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiums = relationship('Premium', back_populates='premiumfile', cascade='all, delete-orphan')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = PremiumFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.premiums.extend([premium.copy() for premium in self.premiums])
        return new

    def __repr__(self):
        return f'<PremiumFile {self.id} {self.name}>'


class Premium(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'premium'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    year = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiumfile_id = Column(Integer, ForeignKey(PremiumFile.id))
    premiumfile = relationship('PremiumFile', back_populates='premiums')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = Premium()
        for attr in ['name', 'year', 'amount']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<Premium {self.id} {self.name}>'


#
class RiskProfileFile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'riskprofilefile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and RiskProfile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='riskprofilefiles')

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofiles = relationship('RiskProfile', back_populates='riskprofilefile', cascade='all, delete-orphan')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = RiskProfileFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.riskprofiles.extend([riskprofile.copy() for riskprofile in self.riskprofiles])
        return new

    def __repr__(self):
        return f'<RiskProfileFile {self.id} {self.name}>'


class RiskProfile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'riskprofile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofilefile_id = Column(Integer, ForeignKey(RiskProfileFile.id))
    riskprofilefile = relationship('RiskProfileFile', back_populates='riskprofiles')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = RiskProfile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<RiskProfile {self.id} {self.name}>'


#
class ModelFile(db.Model):
    __tablename__ = 'modelfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and ModelFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='modelfiles')

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    modelyearlosses = relationship('ModelYearLoss', back_populates='modelfile', cascade='all, delete')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = ModelFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.modelyearlosses.extend([modelyearloss.copy() for modelyearloss in self.modelyearlosses])
        return new

    def __repr__(self):
        return f'<ModelFile {self.id} {self.name}>'


class ModelYearLoss(db.Model):
    __tablename__ = 'modelyearloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)  # For a SL, the amount is a loss ratio, that is a floating point number

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    modelfile_id = Column(Integer, ForeignKey(ModelFile.id))
    modelfile = relationship('ModelFile', back_populates='modelyearlosses')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = ModelYearLoss()
        for attr in ['name', 'year', 'amount']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<ModelYearLoss {self.id} {self.name}>'


#
class PricingRelationship(db.Model):
    # p = PricingRelationship(name='foo', analysis_id=1); session.add(p); session.commit()
    __tablename__ = 'pricingrelationship'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and PricingRelationship
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='pricingrelationships')

    # Define the 1-to-many relationship between PricingRelationship and LayerToModelfile
    layertomodelfiles = relationship('LayerToModelfile', back_populates='pricingrelationship',
                                     cascade='all, delete-orphan')

    # Define the 1-to-many relationship between PricingRelationship and ResultFile
    resultfiles = relationship('ResultFile', back_populates='pricingrelationship', cascade='all, delete-orphan')

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = PricingRelationship()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.layertomodelfiles.extend([layertomodelfile.copy() for layertomodelfile in self.layertomodelfiles])
        return new

    def __repr__(self):
        return f'<PricingRelationship {self.id} {self.name}>'


class LayerToModelfile(db.Model):
    # l = LayerToModelfile(name='foo', pricingrelationship_id=1, layer_id=1, modelfile_id=1); session.add(l); session.commit()
    __tablename__ = 'layertomodelfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between PricingRelationship and LayerToModelfile
    pricingrelationship_id = Column(Integer, ForeignKey(PricingRelationship.id))
    pricingrelationship = relationship('PricingRelationship', back_populates='layertomodelfiles')

    # Define the many-to-many relationship between Layer and ModelFile in the association object LayerToModelfile
    layer_id = Column(Integer, ForeignKey(Layer.id, ondelete='CASCADE'))
    layer = relationship('Layer', backref=backref('layertomodelfiles', passive_deletes=True))

    modelfile_id = Column(Integer, ForeignKey(ModelFile.id, ondelete='CASCADE'))
    modelfile = relationship('ModelFile', backref=backref('layertomodelfiles', passive_deletes=True))

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    def copy(self):
        new = LayerToModelfile()
        for attr in ['name', 'layer_id', 'modelfile_id']:
            setattr(new, attr, getattr(self, attr))
        return new

    def __repr__(self):
        return f'<LayerToModelfile {self.id} {self.name}>'


#
class ResultFile(db.Model):
    __tablename__ = 'resultfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the 1-to-many relationship between Analysis and ResultFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='resultfiles')

    # Define the 1-to-many relationship between PricingRelationship and ResultFile
    pricingrelationship_id = Column(Integer, ForeignKey(PricingRelationship.id))
    pricingrelationship = relationship('PricingRelationship', back_populates='resultfiles')

    # Define the 1-to-many relationhip between ResultFile and ResultYearLoss
    resultyearlosses = relationship('ResultYearLoss', back_populates='resultfile', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ResultFile {self.id} {self.name}>'


#
#     # class ResultLayer(db.Model):
#     #     # TODO: To be defined
#     #     pass
#
#     # class ResultModel(db.Model):
#     #     # TODO: To be defined
#     #     pass
#
class ResultYearLoss(db.Model):
    __tablename__ = 'resultyearloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Define the specific columns
    year = Column(Integer, nullable=False)
    grossloss = Column(Integer)  # Cedant's gross loss
    recovery = Column(Integer)  # Recovery from the reinsurance treaty
    netloss = Column(Integer)  # Cedant's net loss

    # Define the 1-to-many relationhip between ResultFile and ResultYearLoss
    resultfile_id = Column(Integer, ForeignKey(ResultFile.id))
    resultfile = relationship('ResultFile', back_populates='resultyearlosses')

    # Define the 1-to-many relationship between LayerToModelfile and ResultYearLoss
    layertomodelfile_id = Column(Integer, ForeignKey(LayerToModelfile.id))
    layertomodelfile = relationship('LayerToModelfile')

    def __repr__(self):
        return f'<ResultYearLoss {self.id} {self.name}>'
