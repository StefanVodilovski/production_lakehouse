from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    String,
    Text,
    UniqueConstraint,
    JSON,
    func
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class JobCategory(Base):
    __tablename__ = "job_category"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    label = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    job_listings = relationship(
        "JobListing",
        back_populates="category",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "tag",
            "label",
            name="uq_job_category_source_source_category_id",
        ),
    )

class JobListing(Base):
    __tablename__ = "job_listing"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    job_id = Column(String, nullable=False)
    minimum_salary = Column(Float, nullable=True)
    maximum_salary = Column(Float, nullable=True)
    job_post_url = Column(String, nullable=False)
    location = Column(JSON, nullable=True)
    job_title = Column(Text, nullable=False)
    job_created_at = Column(DateTime(timezone=True), nullable=True)
    job_description = Column(Text, nullable=True)
    company = Column(JSON, nullable=True)
    category_id = Column(
        Integer,
        ForeignKey(
            "job_category.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    category = relationship(
        "JobCategory",
        back_populates="job_listings",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "job_id",
            name="uq_job_listing_source_job_id",
        ),
    )