"""add platform name to rom

Revision ID: 1.7.2
Revises: 1.7.1
Create Date: 2023-04-17 12:03:19.163501

"""
import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = '1.7.2'
down_revision = '1.7.1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("roms") as batch_op:
        if os.getenv('ROMM_DB_DRIVER') == 'mariadb':
            batch_op.drop_constraint('PRIMARY', type_="primary")
        batch_op.add_column(sa.Column('p_name', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('url_cover', sa.Text(), nullable=True))
        batch_op.alter_column('name', new_column_name='r_name', type_=sa.String(length=150), existing_type=sa.String(length=150))
        batch_op.alter_column('p_slug', existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column('file_name', existing_type=sa.String(length=450), nullable=False)
    with op.batch_alter_table("roms") as batch_op:
        if os.getenv('ROMM_DB_DRIVER') == 'mariadb':
            batch_op.execute("ALTER TABLE roms ADD COLUMN id INTEGER UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT")
        elif os.getenv('ROMM_DB_DRIVER') == 'sqlite' or not os.getenv('ROMM_DB_DRIVER'):
            batch_op.execute("ALTER TABLE roms RENAME TO old_roms")
            op.create_table('roms',
                sa.Column('id', sa.Integer(), autoincrement=True),
                sa.Column('r_igdb_id', sa.String(length=10), nullable=True),
                sa.Column('p_igdb_id', sa.String(length=10), nullable=True),
                sa.Column('r_sgdb_id', sa.String(length=10), nullable=True),
                sa.Column('p_sgdb_id', sa.String(length=10), nullable=True),
                sa.Column('p_slug', sa.String(length=50), nullable=False),
                sa.Column('p_name', sa.String(length=150), nullable=True),
                sa.Column('file_name', sa.String(length=450), nullable=False),
                sa.Column('file_name_no_tags', sa.String(length=450), nullable=True),
                sa.Column('file_extension', sa.String(length=10), nullable=True),
                sa.Column('file_path', sa.String(length=1000), nullable=True),
                sa.Column('file_size', sa.Float(), nullable=True),
                sa.Column('file_size_units', sa.String(length=10), nullable=True),
                sa.Column('r_name', sa.String(length=350), nullable=True),
                sa.Column('r_slug', sa.String(length=100), nullable=True),
                sa.Column('summary', sa.Text(), nullable=True),
                sa.Column('path_cover_s', sa.Text(), nullable=True),
                sa.Column('path_cover_l', sa.Text(), nullable=True),
                sa.Column('has_cover', sa.Boolean(), nullable=True),
                sa.Column('region', sa.String(length=20), nullable=True),
                sa.Column('revision', sa.String(length=20), nullable=True),
                sa.Column('tags', sa.JSON(), nullable=True),
                sa.Column('multi', sa.Boolean(), nullable=True),
                sa.Column('files', sa.JSON(), nullable=True),
                sa.Column('url_cover', sa.Text(), nullable=True),
                sa.PrimaryKeyConstraint('id')
            )
            batch_op.execute("INSERT INTO roms(\
                                r_igdb_id, p_igdb_id, r_sgdb_id, p_sgdb_id, p_slug, p_name, \
                                file_name, file_name_no_tags, file_extension, file_path, file_size, \
                                file_size_units, r_name, r_slug, summary, path_cover_s, path_cover_l, has_cover, \
                                region, revision, tags, multi, files, url_cover) \
                             SELECT \
                                r_igdb_id, p_igdb_id, r_sgdb_id, p_sgdb_id, p_slug, p_name, \
                                file_name, file_name_no_tags, file_extension, file_path, file_size, \
                                file_size_units, r_name, r_slug, summary, path_cover_s, path_cover_l, has_cover, \
                                region, revision, tags, multi, files, url_cover \
                             FROM old_roms")
            
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("roms") as batch_op:
        batch_op.drop_constraint('PRIMARY', type_="primary")
        batch_op.drop_column('id')
        batch_op.drop_column('p_name')
        batch_op.drop_column('url_cover')
        batch_op.alter_column('r_name', new_column_name='name', type_=sa.String(length=150), existing_type=sa.String(length=150))
        batch_op.alter_column('p_slug', existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column('file_name', existing_type=sa.String(length=450), nullable=False)
    # ### end Alembic commands ###
