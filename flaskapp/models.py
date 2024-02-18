"""
Commands for testing:

rm .\migrations\; flask db init; flask db migrate; flask db upgrade; $env:POSTGRES_HOST='localhost'; $env:POSTGRES_USER='postgres'; $env:POSTGRES_PASSWORD='a'; $env:POSTGRES_DB='app_db'; $env:SECRET_KEY='38ee1bfef77c029614cc87c3ac922f2de08f44cd75ed6e41f31477f831a1cef4'
python
from app import app; app.app_context().push(); from flaskapp.extensions import *; from flaskapp.models import *; session = db.session; import os; os.system('cls')


This module defines a set of SQLAlchemy database models representing a modeling and pricing system

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
- ResultYearLoss: Represents individual year loss records in analysis results.

These models are designed to work with SQLAlchemy and are used to interact with the underlying database.

Resources:
- Duplicate records: https://stackoverflow.com/questions/44061006/sqlalchemy-how-to-copy-deep-copy-a-entry-and-all-its-foreign-relation
- Reference: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many
- https://stackoverflow.com/questions/30406808/flask-sqlalchemy-difference-between-association-model-and-association-table-fo
- https://stackoverflow.com/questions/68322485/conflicts-with-relationship-between-tables
- https://docs.sqlalchemy.org/en/14/orm/backref.html. TL;DR:Do not use backref, use the bidirectional back_populates attribute!
- https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#association-pattern
- Explanations on session add (register the operations to the object in the session), flush (pass them on to the DB) and commit (persist the operations in the DB): https://stackoverflow.com/questions/4201455/sqlalchemy-whats-the-difference-between-flush-and-commit

"""

from flaskapp.extensions import db
from typing import Final
from typing import List
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy.orm import validates
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.associationproxy import AssociationProxy


class CommonMixin:
    """ Define a series of common elements that may be applied to mapped
        classes using this class as a mixin class """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    def __repr__(self):
        # https://stackoverflow.com/questions/610883/how-to-check-if-an-object-has-an-attribute/610923#610923
        try:
            return f'<{self.__class__.__name__} {self.id} {self.name}>'
        except AttributeError:
            return f'<{self.__class__.__name__} {self.id}>'


class Analysis(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    quote: Mapped[int] = mapped_column(nullable=False)
    client: Mapped[str] = mapped_column(String(50), nullable=False)

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

    # Define the 1-to-many relationship between Analysis and Layer, HistoLossFile, PremiumFile, RiskProfileFile, ModelFile, PricingRelationship, ResultFile
    layers: Mapped[List['Layer']] = relationship(back_populates='analysis', cascade='all, delete-orphan')
    histolossfiles: Mapped[List['HistoLossFile']] = \
        relationship(back_populates='analysis', cascade='all, delete-orphan')
    premiumfiles: Mapped[List['PremiumFile']] = relationship(back_populates='analysis', cascade='all, delete-orphan')
    riskprofilefiles: Mapped[List['RiskProfileFile']] = \
        relationship(back_populates='analysis', cascade='all, delete-orphan')
    modelfiles: Mapped[List['ModelFile']] = relationship(back_populates='analysis', cascade='all, delete-orphan')
    resultfiles: Mapped[List['ResultFile']] = relationship(back_populates='analysis', cascade='all, delete-orphan')

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


class Layer(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    premium: Mapped[int] = mapped_column(nullable=False)
    agg_limit: Mapped[int] = mapped_column(nullable=False)
    agg_deduct: Mapped[int] = mapped_column(nullable=False)
    display_order: Mapped[int] = mapped_column()

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The layer name must be entered')
        return value

    @validates('premium', 'agg_limit', 'agg_deduct')
    def validate_int_col(self, key, value):
        if value is None:
            raise ValueError('The premiums, deductibles and limits must be entered for all layers')
        if not str(value).isdigit():
            raise ValueError('The premiums, deductibles and limits must all be integers')
        return value

    # Define the 1-to-many relationship between Analysis and Layer
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='layers')

    # Get the modelfiles associated to the layer through the association layer_modelfile_table
    modelfiles: Mapped[List['ModelFile']] = relationship(secondary=lambda: layer_modelfile_table)

    def copy(self):
        new = Layer()
        for attr in ['name', 'premium', 'deductible', 'limit', 'display_order']:
            setattr(new, attr, getattr(self, attr))
        return new


class HistoLossFile(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    vintage: Mapped[int] = mapped_column(nullable=False)

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
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='histolossfiles')

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    losses: Mapped[List['HistoLoss']] = relationship(back_populates='lossfile', cascade='all, delete-orphan')

    def copy(self):
        new = HistoLossFile()
        for attr in ['name', 'vintage']:
            setattr(new, attr, getattr(self, attr))
        new.losses.extend([loss.copy() for loss in self.losses])
        return new


class HistoLoss(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(nullable=False)
    premium: Mapped[int] = mapped_column()
    loss: Mapped[int] = mapped_column()
    loss_ratio: Mapped[float] = mapped_column()

    # Define the 1-to-many relationship between HistoLossFile and HistoLoss
    lossfile_id: Mapped[int] = mapped_column(ForeignKey('histolossfile.id'))
    lossfile: Mapped['HistoLossFile'] = relationship(back_populates='losses')

    def copy(self):
        new = HistoLoss()
        for attr in ['year', 'premium', 'loss', 'loss_ratio']:
            setattr(new, attr, getattr(self, attr))
        return new


class PremiumFile(CommonMixin, db.Model):  # This model is not necessary for SL pricing
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    # Define the 1-to-many relationship between Analysis and PremiumFile
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='premiumfiles')

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiums: Mapped[List['Premium']] = relationship(back_populates='premiumfile', cascade='all, delete-orphan')

    def copy(self):
        new = PremiumFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.premiums.extend([premium.copy() for premium in self.premiums])
        return new


class Premium(CommonMixin, db.Model):  # This model is not necessary for SL pricing
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)

    # Define the 1-to-many relationship between PremiumFile and Premium
    premiumfile_id: Mapped[int] = mapped_column(ForeignKey('premiumfile.id'))
    premiumfile: Mapped['PremiumFile'] = relationship(back_populates='premiums')

    def copy(self):
        new = Premium()
        for attr in ['name', 'year', 'amount']:
            setattr(new, attr, getattr(self, attr))
        return new


class RiskProfileFile(CommonMixin, db.Model):  # This model is not necessary for SL pricing
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    # Define the 1-to-many relationship between Analysis and RiskProfile
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='riskprofilefiles')

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofiles: Mapped[List['RiskProfile']] = relationship(back_populates='riskprofilefile',
                                                             cascade='all, delete-orphan')

    def copy(self):
        new = RiskProfileFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.riskprofiles.extend([riskprofile.copy() for riskprofile in self.riskprofiles])
        return new


class RiskProfile(CommonMixin, db.Model):  # This model is not necessary for SL pricing
    id: Mapped[int] = mapped_column(primary_key=True)

    # Define the 1-to-many relationship between RiskProfileFile and RiskProfile
    riskprofilefile_id: Mapped[int] = mapped_column(ForeignKey('riskprofilefile.id'))
    riskprofilefile: Mapped['RiskProfileFile'] = relationship(back_populates='riskprofiles')

    def copy(self):
        new = RiskProfile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        return new


class ModelFile(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Cat/Non cat

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    # Define the 1-to-many relationship between Analysis and ModelFile
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='modelfiles')

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    yearlosses: Mapped[List['ModelYearLoss']] = relationship(back_populates='modelfile', cascade='all, delete-orphan')

    def copy(self):
        new = ModelFile()
        for attr in ['name']:
            setattr(new, attr, getattr(self, attr))
        new.modelyearlosses.extend([modelyearloss.copy() for modelyearloss in self.modelyearlosses])
        return new


class ModelYearLoss(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(nullable=False)
    loss_ratio: Mapped[float] = mapped_column()

    # Define the 1-to-many relationship between ModelFile and ModelYearLoss
    modelfile_id: Mapped[int] = mapped_column(ForeignKey('modelfile.id'))
    modelfile: Mapped['ModelFile'] = relationship(back_populates='yearlosses')

    def copy(self):
        new = ModelYearLoss()
        for attr in ['name', 'year', 'amount']:
            setattr(new, attr, getattr(self, attr))
        return new


layer_modelfile_table: Final[Table] = Table(
    'layer_modelfile',
    db.metadata,
    Column('layer_id', ForeignKey('layer.id'), primary_key=True),
    Column('modelfile_id', ForeignKey('modelfile.id'), primary_key=True),
)


class ResultFile(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        if not value:
            raise ValueError(f'The name must be entered')
        return value

    # Define the 1-to-many relationship between Analysis and ResultFile
    analysis_id: Mapped[int] = mapped_column1(ForeignKey('analysis.id'))
    analysis: Mapped['Analysis'] = relationship(back_populates='resultfiles')

    # Define the 1-to-many relationship between ResultFile and ResultLayer, ResultModelFile
    layers: Mapped[List['ResultLayer']] = relationship(back_populates='resultfile', cascade='all, delete-orphan')
    modelfiles: Mapped[List['ResultModelFile']] = relationship(back_populates='resultfile',
                                                               cascade='all, delete-orphan')


class ResultLayer(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    premium: Mapped[int] = mapped_column(nullable=False)
    agg_limit: Mapped[int] = mapped_column(nullable=False)
    agg_deduct: Mapped[int] = mapped_column(nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The layer name must be entered')
        return value

    @validates('premium', 'agg_limit', 'agg_deduct')
    def validate_int_col(self, key, value):
        if value is None:
            raise ValueError('The premiums, deductibles and limits must be entered for all layers')
        if not str(value).isdigit():
            raise ValueError('The premiums, deductibles and limits must all be integers')
        return value

    # Define the 1-to-many relationship between ResultFile and ResultLayer
    resultfile_id: Mapped[int] = mapped_column(ForeignKey('resultfile.id'))
    resultfile: Mapped['ResultFile'] = relationship(back_populates='layers')

    # Get the modelfiles associated to the resultlayer through the association result_layer_modelfile_table
    modelfiles: Mapped[List['ResultModelFile']] = relationship(secondary=lambda: result_layer_modelfile_table)

    # Define the 1-to-many relationship between ResultLayer and ResultYearLoss
    yearlosses: Mapped[List['ResultLayerYearLoss']] = relationship(back_populates='layer', cascade='all, delete-orphan')


class ResultLayerXS(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    premium: Mapped[int] = mapped_column(nullable=False)
    occ_limit: Mapped[int] = mapped_column(nullable=False)
    occ_deduct: Mapped[int] = mapped_column()
    agg_limit: Mapped[int] = mapped_column(nullable=False)
    agg_deduct: Mapped[int] = mapped_column(nullable=False)

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The layer name must be entered')
        return value

    @validates('premium', 'agg_limit', 'agg_deduct')
    def validate_int_col(self, key, value):
        if value is None:
            raise ValueError('The premiums, deductibles and limits must be entered for all layers')
        if not str(value).isdigit():
            raise ValueError('The premiums, deductibles and limits must all be integers')
        return value

    # Define the 1-to-many relationship between ResultFile and ResultLayer
    resultfile_id: Mapped[int] = mapped_column(ForeignKey('resultfile.id'))
    resultfile: Mapped['ResultFile'] = relationship(back_populates='layers')

    # Get the modelfiles associated to the resultlayer through the association result_layer_modelfile_table
    modelfiles: Mapped[List['ResultModelFile']] = relationship(secondary=lambda: result_layer_modelfile_table)

    # Define the 1-to-many relationship between ResultLayer and ResultYearLoss
    # TODO: Create ResultLayerYearLossXS
    yearlosses: Mapped[List['ResultLayerYearLossXS']] = relationship(back_populates='layer',
                                                                     cascade='all, delete-orphan')


class ResultLayerYearLoss(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Cat/Non cat
    loss_ratio: Mapped[float] = mapped_column()
    gross: Mapped[int] = mapped_column()
    ceded: Mapped[int] = mapped_column()
    net: Mapped[int] = mapped_column()

    # Define the 1-to-many relationship between ResultLayer and ResultYearLoss
    resultlayer_id: Mapped[int] = mapped_column(ForeignKey('resultlayer.id'))
    layer: Mapped['ResultLayer'] = relationship(back_populates='yearlosses')


class ResultModelFile(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    id_src: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # Cat/Non cat

    @validates('name')
    def validate_name(self, key, value):
        if value is None or not value:
            raise ValueError('The layer name must be entered')
        return value

    # Define the 1-to-many relationship between ResultFile and ResultModelFile
    resultfile_id: Mapped[int] = mapped_column(ForeignKey('resultfile.id'))
    resultfile: Mapped['ResultFile'] = relationship(back_populates='modelfiles')

    # Define the 1-to-many relationship between ResultModelFile and ResultModelYearLoss
    yearlosses: Mapped[List['ResultModelYearLoss']] = relationship(back_populates='modelfile',
                                                                   cascade='all, delete-orphan')


class ResultModelYearLoss(CommonMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(nullable=False)
    loss_ratio: Mapped[float] = mapped_column()

    # Define the 1-to-many relationship between ResultModelFile and ResultModelYearLoss
    resultmodelfile_id: Mapped[int] = mapped_column(ForeignKey('resultmodelfile.id'))
    modelfile: Mapped['ResultModelFile'] = relationship(back_populates='yearlosses')


result_layer_modelfile_table: Final[Table] = Table(
    'result_layer_modelfile',
    db.metadata,
    Column('resultlayer_id', ForeignKey('resultlayer.id'), primary_key=True),
    Column('modelfile_id', ForeignKey('resultmodelfile.id'), primary_key=True),
)
