from orator.migrations import Migration


class AddLogAttachmentIdToSimulationsTable(Migration):

    def up(self):
        with self.schema.table('simulations') as table:
            table.big_integer('log_attachment_id').nullable()

    def down(self):
        with self.schema.table('simulations') as table:
            table.drop_column('log_attachment_id')

