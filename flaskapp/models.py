"""
Commands for testing:

rm .\migrations\; flask db init; flask db migrate; flask db upgrade; python
$env:POSTGRES_HOST='localhost'; $env:POSTGRES_USER='postgres'; $env:POSTGRES_PASSWORD='a'; $env:POSTGRES_DB='app_db'; $env:SECRET_KEY='38ee1bfef77c029614cc87c3ac922f2de08f44cd75ed6e41f31477f831a1cef4'
from app import app; app.app_context().push(); from flaskapp.extensions import *; from flaskapp.models import *; session = db.session


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

"""

from flaskapp.extensions import db
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import validates, relationship, backref


class Analysis(db.Model):
    __tablename__ = 'analysis'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    quote = Column(Integer)
    client = Column(String(50))

    # Validate the input data
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
            raise ValueError('The analysis client must be entered')
        return value

    # Define the 1-to-many relationship between Analysis and Layer, HistoLossFile, PremiumFile, RiskProfileFile, ModelFile, PricingRelationship, ResultFile
    layers = relationship('Layer', back_populates='analysis', cascade='all, delete-orphan')
    histolossfiles = relationship('HistoLossFile', back_populates='analysis', cascade='all, delete-orphan')
    premiumfiles = relationship('PremiumFile', back_populates='analysis', cascade='all, delete-orphan')
    riskprofilefiles = relationship('RiskProfileFile', back_populates='analysis', cascade='all, delete-orphan')
    modelfiles = relationship('ModelFile', back_populates='analysis', cascade='all, delete-orphan')
    pricingrelationships = relationship('PricingRelationship', back_populates='analysis', cascade='all, delete-orphan')
    resultfiles = relationship('ResultFile', back_populates='analysis', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'

    def copy(self):
        new = Analysis()
        new.name = self.name
        new.quote = self.quote
        new.client = self.client
        for layer in self.layers:
            new.layers.append(layer.copy())
        return new


class Layer(db.Model):
    __tablename__ = 'layer'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    premium = Column(Integer)
    deductible = Column(Integer)
    limit = Column(Integer)
    display_order = Column(Integer)

    # Validate the input data
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

    # Define the 1-to-many relationship between Analysis and Layer
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='layers')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'

    def copy(self):
        new = Layer()
        new.name = self.name
        new.premium = self.premium
        new.deductible = self.deductible
        new.limit = self.limit
        new.display_order = self.display_order
        new.analysis_id = self.analysis_id
        return new


class HistoLossFile(db.Model):
    __tablename__ = 'histolossfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    vintage = Column(Integer)

    # Validate the input data
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

    # Define the 1-to-many relationship between Analysis and HistoLossFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='histolossfiles')

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    losses = relationship('HistoLoss', back_populates='lossfile', cascade='all, delete')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class HistoLoss(db.Model):
    __tablename__ = 'histoloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    year = Column(Integer)
    premium = Column(Integer)
    loss = Column(Integer)
    loss_ratio = Column(Float)

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    lossfile_id = Column(Integer, ForeignKey(HistoLossFile.id))
    lossfile = relationship('HistoLossFile', back_populates='losses')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class PremiumFile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'premiumfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between Analysis and PremiumFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='premiumfiles')

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiums = relationship('Premium', back_populates='premiumfile', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class Premium(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'premium'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    year = Column(Integer)
    amount = Column(Integer)

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiumfile_id = Column(Integer, ForeignKey(PremiumFile.id))
    premiumfile = relationship('PremiumFile', back_populates='premiums')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class RiskProfileFile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'riskprofilefile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between Analysis and RiskProfile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='riskprofilefiles')

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofiles = relationship('RiskProfile', back_populates='riskprofilefile', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class RiskProfile(db.Model):  # This model is not necessary for SL pricing
    __tablename__ = 'riskprofile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofilefile_id = Column(Integer, ForeignKey(RiskProfileFile.id))
    riskprofilefile = relationship('RiskProfileFile', back_populates='riskprofiles')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class ModelFile(db.Model):
    __tablename__ = 'modelfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between Analysis and ModelFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='modelfiles')

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    modelyearlosses = relationship('ModelYearLoss', back_populates='modelfile', cascade='all, delete')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class ModelYearLoss(db.Model):
    __tablename__ = 'modelyearloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    year = Column(Integer)
    amount = Column(Float)  # For a SL, the amount is a loss ratio, that is a floating point number

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    modelfile_id = Column(Integer, ForeignKey(ModelFile.id))
    modelfile = relationship('ModelFile', back_populates='modelyearlosses')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class PricingRelationship(db.Model):
    __tablename__ = 'pricingrelationship'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between Analysis and PricingRelationship
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='pricingrelationships')

    # Define the 1-to-many relationship between PricingRelationship and ResultFile
    resultfiles = relationship('ResultFile', back_populates='pricingrelationship', cascade='all, delete-orphan')

    # Define the 1-to-many relationship between PricingRelationship and LayerToModelfile
    layertomodelfiles = relationship('LayerToModelfile', back_populates='pricingrelationship',
                                     cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class LayerToModelfile(db.Model):
    __tablename__ = 'layertomodelfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between PricingRelationship and LayerToModelfile
    pricingrelationship_id = Column(Integer, ForeignKey(PricingRelationship.id))
    pricingrelationship = relationship('PricingRelationship', back_populates='layertomodelfiles')

    # Define the many-to-many relationship between Layer and ModelFile in the association object LayerToModelfile
    layer_id = Column(Integer, ForeignKey(Layer.id))
    layer = relationship('Layer')

    modelfile_id = Column(Integer, ForeignKey(ModelFile.id))
    modelfile = relationship('ModelFile')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class ResultFile(db.Model):
    __tablename__ = 'resultfile'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the 1-to-many relationship between Analysis and ResultFile
    analysis_id = Column(Integer, ForeignKey(Analysis.id))
    analysis = relationship('Analysis', back_populates='resultfiles')

    # Define the 1-to-many relationship between PricingRelationship and ResultFile
    pricingrelationship_id = Column(Integer, ForeignKey(PricingRelationship.id))
    pricingrelationship = relationship('PricingRelationship', back_populates='resultfiles')

    # Define the 1-to-many relationhip between ResultFile and ResultYearLoss
    resultyearlosses = relationship('ResultYearLoss', back_populates='resultfile', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'


class ResultYearLoss(db.Model):
    __tablename__ = 'resultyearloss'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # Define the specific columns
    year = Column(Integer)
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
        return f'<{self.__tablename__.capitalize()} {self.id} {self.name}>'
