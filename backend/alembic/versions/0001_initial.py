"""Initial database schema.

Revision ID: 0001_initial
Revises: None
Create Date: 2026-06-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
default_schema = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            email VARCHAR(320) NOT NULL UNIQUE,
            full_name VARCHAR(128),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE source_documents (
            id UUID PRIMARY KEY,
            owner_id UUID REFERENCES users(id),
            title VARCHAR(256) NOT NULL,
            source_url VARCHAR(2048),
            file_name VARCHAR(256),
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY,
            source_document_id UUID NOT NULL REFERENCES source_documents(id),
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding vector(1536) NOT NULL,
            search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE chat_threads (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            title VARCHAR(256),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE chat_messages (
            id UUID PRIMARY KEY,
            thread_id UUID NOT NULL REFERENCES chat_threads(id),
            sender VARCHAR(32) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE message_citations (
            id UUID PRIMARY KEY,
            message_id UUID NOT NULL REFERENCES chat_messages(id),
            source_document_id UUID NOT NULL REFERENCES source_documents(id),
            document_chunk_id UUID REFERENCES document_chunks(id),
            excerpt TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX ix_source_documents_owner_id ON source_documents (owner_id)")
    op.execute("CREATE INDEX ix_document_chunks_source_document_id ON document_chunks (source_document_id)")
    op.execute("CREATE INDEX ix_chat_threads_user_id ON chat_threads (user_id)")
    op.execute("CREATE INDEX ix_chat_messages_thread_id ON chat_messages (thread_id)")
    op.execute("CREATE INDEX ix_message_citations_message_id ON message_citations (message_id)")
    op.execute("CREATE INDEX ix_message_citations_source_document_id ON message_citations (source_document_id)")
    op.execute("CREATE INDEX ix_message_citations_document_chunk_id ON message_citations (document_chunk_id)")

    op.execute(
        "CREATE INDEX document_chunks_embedding_hnsw_idx ON document_chunks USING hnsw (embedding vector_l2_ops)"
    )
    op.execute(
        "CREATE INDEX document_chunks_search_vector_gin ON document_chunks USING gin (search_vector)"
    )

    op.execute("ALTER TABLE chat_threads ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY select_chat_threads ON chat_threads FOR SELECT USING (user_id = auth.uid()::uuid)"
    )
    op.execute(
        "CREATE POLICY insert_chat_threads ON chat_threads FOR INSERT WITH CHECK (user_id = auth.uid()::uuid)"
    )
    op.execute(
        "CREATE POLICY update_chat_threads ON chat_threads FOR UPDATE USING (user_id = auth.uid()::uuid) WITH CHECK (user_id = auth.uid()::uuid)"
    )
    op.execute(
        "CREATE POLICY delete_chat_threads ON chat_threads FOR DELETE USING (user_id = auth.uid()::uuid)"
    )

    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY select_chat_messages ON chat_messages FOR SELECT USING (thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid()::uuid))"
    )
    op.execute(
        "CREATE POLICY insert_chat_messages ON chat_messages FOR INSERT WITH CHECK (thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid()::uuid))"
    )
    op.execute(
        "CREATE POLICY update_chat_messages ON chat_messages FOR UPDATE USING (thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid()::uuid)) WITH CHECK (thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid()::uuid))"
    )
    op.execute(
        "CREATE POLICY delete_chat_messages ON chat_messages FOR DELETE USING (thread_id IN (SELECT id FROM chat_threads WHERE user_id = auth.uid()::uuid))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY delete_chat_messages ON chat_messages")
    op.execute("DROP POLICY update_chat_messages ON chat_messages")
    op.execute("DROP POLICY insert_chat_messages ON chat_messages")
    op.execute("DROP POLICY select_chat_messages ON chat_messages")
    op.execute("ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY delete_chat_threads ON chat_threads")
    op.execute("DROP POLICY update_chat_threads ON chat_threads")
    op.execute("DROP POLICY insert_chat_threads ON chat_threads")
    op.execute("DROP POLICY select_chat_threads ON chat_threads")
    op.execute("ALTER TABLE chat_threads DISABLE ROW LEVEL SECURITY")

    op.execute("DROP INDEX IF EXISTS document_chunks_search_vector_gin")
    op.execute("DROP INDEX IF EXISTS document_chunks_embedding_hnsw_idx")
    op.execute("DROP INDEX IF EXISTS ix_message_citations_document_chunk_id")
    op.execute("DROP INDEX IF EXISTS ix_message_citations_source_document_id")
    op.execute("DROP INDEX IF EXISTS ix_message_citations_message_id")
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_thread_id")
    op.execute("DROP INDEX IF EXISTS ix_chat_threads_user_id")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_source_document_id")
    op.execute("DROP INDEX IF EXISTS ix_source_documents_owner_id")

    op.drop_table("message_citations")
    op.drop_table("chat_messages")
    op.drop_table("chat_threads")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("users")
