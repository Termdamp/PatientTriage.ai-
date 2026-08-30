"""initial

Revision ID: 0001
Revises:
Create Date: 2026-08-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('capacity',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('total_beds', sa.Integer(), nullable=False),
    sa.Column('occupied_beds', sa.Integer(), nullable=False),
    sa.Column('critical_beds', sa.Integer(), nullable=False),
    sa.Column('critical_occupied', sa.Integer(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('patients',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('gender', sa.String(), nullable=False),
    sa.Column('chief_complaint', sa.String(), nullable=False),
    sa.Column('symptoms', sa.JSON(), nullable=False),
    sa.Column('medical_history', sa.JSON(), nullable=True),
    sa.Column('history_available', sa.Boolean(), nullable=False),
    sa.Column('arrival_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('WAITING', 'IN_REVIEW', 'IN_TREATMENT', 'COMPLETED', name='patientstatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('alerts',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('patient_id', sa.String(), nullable=True),
    sa.Column('type', sa.Enum('DETERIORATION', 'WAITING_BREACH', 'CAPACITY', 'SYSTEM', name='alerttype'), nullable=False),
    sa.Column('severity', sa.Enum('CRITICAL', 'WARNING', 'INFO', name='alertseverity'), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('acknowledged', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assessments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('patient_id', sa.String(), nullable=False),
    sa.Column('risk_score', sa.Float(), nullable=False),
    sa.Column('priority', sa.Enum('CRITICAL', 'HIGH', 'MODERATE', 'LOW', name='priority'), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('safety_floor', sa.Enum('CRITICAL', 'HIGH', 'MODERATE', 'LOW', name='priority'), nullable=True),
    sa.Column('reasons', sa.JSON(), nullable=False),
    sa.Column('recommended_action', sa.Enum('IMMEDIATE_CLINICIAN_REASSESSMENT', 'URGENT_CLINICIAN_REVIEW', 'CLINICIAN_REVIEW', 'ROUTINE_REVIEW', name='recommendedaction'), nullable=False),
    sa.Column('model_version', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('deteriorating', sa.Integer(), nullable=False),
    sa.Column('deterioration_severity', sa.String(), nullable=True),
    sa.Column('safety_flags', sa.JSON(), nullable=False),
    sa.Column('age_group', sa.String(), nullable=True),
    sa.Column('data_quality', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('audit_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('patient_id', sa.String(), nullable=True),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('actor', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('overrides',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('patient_id', sa.String(), nullable=False),
    sa.Column('assessment_id', sa.String(), nullable=False),
    sa.Column('original_priority', sa.Enum('CRITICAL', 'HIGH', 'MODERATE', 'LOW', name='priority'), nullable=False),
    sa.Column('new_priority', sa.Enum('CRITICAL', 'HIGH', 'MODERATE', 'LOW', name='priority'), nullable=False),
    sa.Column('reason', sa.String(), nullable=False),
    sa.Column('clinician_id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('vitals',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('patient_id', sa.String(), nullable=False),
    sa.Column('heart_rate', sa.Float(), nullable=True),
    sa.Column('systolic_bp', sa.Float(), nullable=True),
    sa.Column('diastolic_bp', sa.Float(), nullable=True),
    sa.Column('spo2', sa.Float(), nullable=True),
    sa.Column('temperature', sa.Float(), nullable=True),
    sa.Column('respiratory_rate', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('vitals')
    op.drop_table('overrides')
    op.drop_table('audit_events')
    op.drop_table('assessments')
    op.drop_table('alerts')
    op.drop_table('patients')
    op.drop_table('capacity')
