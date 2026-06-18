<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div class="display-1">
        Magnets from MagnetDB
      </div>
      <router-link class="btn btn-success" :to="{ name: 'new_magnet' }">
        New magnet
      </router-link>
    </div>

    <Card>
      <DataTable
        :headers="headers" @fetch="fetch" config-persistence-key="magnet-list"
        @item-selected="$router.push({ name: 'magnet', params: { id: $event.id } })"
      >
        <template v-slot:item.name="{ item }">
          {{ item.name }}
        </template>
        <template v-slot:item.description="{ item }">
          <template v-if="item.description">{{ item.description }}</template>
          <span v-else class="text-gray-500 italic">Not available</span>
        </template>
        <template v-slot:item.status="{ item }">
          <StatusBadge :status="item.status"></StatusBadge>
        </template>
        <template v-slot:item.design_office_reference="{ item }">
          <template v-if="item.design_office_reference">{{ item.design_office_reference }}</template>
          <span v-else class="text-gray-500 italic">Not available</span>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ $filters.datetime(item.created_at) }}
        </template>
        <template v-slot:item.updated_at="{ item }">
          {{ $filters.datetime(item.updated_at) }}
        </template>
        <template v-slot:item.commissioned_at="{ item }">
          {{ $filters.datetime(item.commissioned_at) }}
        </template>
        <template v-slot:item.decommissioned_at="{ item }">
          {{ $filters.datetime(item.decommissioned_at) }}
        </template>
      </DataTable>
    </Card>
  </div>
</template>

<script>
import * as magnetService from '@/services/magnetService'
import Card from '@/components/Card'
import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";

export default {
  name: 'MagnetList',
  components: {
    Card,
    DataTable,
    StatusBadge,
  },
  data() {
    return {
      headers: [
        {
          key: 'name',
          name: 'Name',
          default: true,
          sortable: true,
        },
        {
          key: 'description',
          name: 'Description',
          default: true,
        },
        {
          key: 'status',
          name: 'Status',
        },
        {
          key: 'design_office_reference',
          name: 'Design Office Reference',
        },
        {
          key: 'created_at',
          name: 'Created At',
          default: true,
          sortable: true,
        },
        {
          key: 'updated_at',
          name: 'Updated At',
          sortable: true,
        },
        {
          key: 'commissioned_at',
          name: 'Commissioned At',
          sortable: true,
        },
        {
          key: 'decommissioned_at',
          name: 'Decommissioned At',
          sortable: true,
        },
      ]
    }
  },
  methods: {
    fetch({ query, page, perPage, sortBy, sortDesc }) {
      return magnetService.list({ query, page, perPage, sortBy, sortDesc }).then((res) => ({
        currentPage: res.current_page,
        lastPage: res.last_page,
        items: res.items,
        perPage,
        query,
        sortBy,
        sortDesc: sortDesc === null ? true : sortDesc,
      }))
    },
  },
}
</script>
