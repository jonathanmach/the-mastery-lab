from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Concept(Base):
    """OMOP vocabulary table — stores human-readable labels for all coded values."""

    __tablename__ = "concept"
    __table_args__ = (UniqueConstraint("vocabulary_id", "concept_code"),)

    concept_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_name: Mapped[str] = mapped_column(String(500))           # human-readable label
    domain_id: Mapped[str] = mapped_column(String(20))               # "Condition", "Drug", "Measurement", "Observation"
    vocabulary_id: Mapped[str] = mapped_column(String(20))           # "SNOMED", "RxNorm", "LOINC", "ICD10CM"
    concept_code: Mapped[str] = mapped_column(String(50))            # raw source code


class Person(Base):
    __tablename__ = "person"

    person_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gender_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    year_of_birth: Mapped[int] = mapped_column(Integer)
    month_of_birth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_birth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    ethnicity_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    person_source_value: Mapped[str] = mapped_column(String(255), unique=True)  # FHIR patient ID
    gender_source_value: Mapped[str | None] = mapped_column(String(50), nullable=True)

    observation_periods: Mapped[list["ObservationPeriod"]] = relationship(back_populates="person")
    visit_occurrences: Mapped[list["VisitOccurrence"]] = relationship(back_populates="person")


class ObservationPeriod(Base):
    __tablename__ = "observation_period"

    observation_period_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    observation_period_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    observation_period_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)  # EHR

    person: Mapped["Person"] = relationship(back_populates="observation_periods")


class VisitOccurrence(Base):
    __tablename__ = "visit_occurrence"

    visit_occurrence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    visit_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    visit_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    visit_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    visit_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)
    visit_source_value: Mapped[str] = mapped_column(String(255))  # FHIR encounter ID

    person: Mapped["Person"] = relationship(back_populates="visit_occurrences")


class ConditionOccurrence(Base):
    __tablename__ = "condition_occurrence"

    condition_occurrence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    condition_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    condition_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    condition_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    condition_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)
    condition_source_value: Mapped[str | None] = mapped_column(String(255), nullable=True)  # SNOMED code
    visit_occurrence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("visit_occurrence.visit_occurrence_id"), nullable=True
    )


class DrugExposure(Base):
    __tablename__ = "drug_exposure"

    drug_exposure_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    drug_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    drug_exposure_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    drug_exposure_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    drug_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)
    drug_source_value: Mapped[str | None] = mapped_column(String(255), nullable=True)  # RxNorm code
    visit_occurrence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("visit_occurrence.visit_occurrence_id"), nullable=True
    )


class Measurement(Base):
    __tablename__ = "measurement"

    measurement_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    measurement_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    measurement_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)
    value_as_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    measurement_source_value: Mapped[str | None] = mapped_column(String(255), nullable=True)  # LOINC code
    visit_occurrence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("visit_occurrence.visit_occurrence_id"), nullable=True
    )


class Observation(Base):
    __tablename__ = "observation"

    observation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"), nullable=False)
    observation_concept_id: Mapped[int] = mapped_column(Integer, default=0)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    observation_type_concept_id: Mapped[int] = mapped_column(Integer, default=32817)
    value_as_string: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observation_source_value: Mapped[str | None] = mapped_column(String(255), nullable=True)  # LOINC code
    visit_occurrence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("visit_occurrence.visit_occurrence_id"), nullable=True
    )
