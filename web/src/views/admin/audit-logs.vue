<template>
  <div>
    <div class="display-1 mb-6">
      Audit Logs
    </div>

    <Card>
      <DataTable :headers="headers" @fetch="fetch">
        <template v-slot:item.created_at="{ item }">
          {{ datetime(item.created_at) }}
        </template>
        <template v-slot:item.message="{ item }">
          {{ item.message }}
        </template>
        <template v-slot:item.resource="{ item }">
          <span v-if="item.resource_name">{{ item.resource_name }}</span>
          <span v-else class="italic">Unknown</span>
          <span v-if="item.resource_id" class="text-gray-500">
            ({{ item.resource_type }}_{{ item.resource_id }})
          </span>
        </template>
        <template v-slot:item.user="{ item }">
          <template v-if="item.user">
            {{ item.user.name }} <span class="text-gray-500">({{ item.user.username }})</span>
          </template>
          <span v-else class="italic">Unavailable</span>
        </template>
      </DataTable>
    </Card>
  </div>
</template>

<script>
import { useFilters } from '@/composables/useFilters'
import * as auditLogService from '@/services/admin/auditLogService'
import Card from '@/components/Card'
import DataTable from "@/components/DataTable";

export default {
  name: 'AuditLogs',
  setup() {
    const { datetime } = useFilters()
    return { datetime }
  },
  components: {
    DataTable,
    Card,
  },
  data() {
    return {
      headers: [
        {
          key: 'created_at',
          name: 'Date',
          default: true,
          sortable: true,
        },
        {
          key: 'message',
          name: 'Message',
          default: true,
        },
        {
          key: 'user',
          name: 'User',
          default: true,
        },
        {
          key: 'resource',
          name: 'Resource',
          default: true,
        },
      ]
    }
  },
  methods: {
    fetch({ query, page, perPage, sortBy, sortDesc }) {
      return auditLogService.list({ query, page, perPage, sortBy, sortDesc }).then((res) => ({
        currentPage: res.current_page,
        lastPage: res.last_page,
        items: res.items,
        perPage,
        query,
        sortBy: sortBy === null ? 'created_at' : sortBy,
        sortDesc: sortDesc === null ? true : sortDesc,
      }))
    },
  },
}
</script>
