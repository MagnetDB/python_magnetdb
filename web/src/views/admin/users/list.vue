<template>
  <div>
    <div class="display-1 mb-6">
      Users
    </div>

    <Card>
      <DataTable
        :headers="headers" @fetch="fetch"
        @item-selected="$router.push({ name: 'admin_user', params: { id: $event.id } })"
      >
        <template v-slot:item.id="{ item }">
          {{ item.id }}
        </template>
        <template v-slot:item.username="{ item }">
          {{ item.username }}
        </template>
        <template v-slot:item.name="{ item }">
          {{ item.name }}
        </template>
        <template v-slot:item.email="{ item }">
          {{ item.email }}
        </template>
        <template v-slot:item.role="{ item }">
          {{ $filters.roleName(item.role) }}
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ $filters.datetime(item.created_at) }}
        </template>
        <template v-slot:item.updated_at="{ item }">
          {{ $filters.datetime(item.updated_at) }}
        </template>
      </DataTable>
    </Card>
  </div>
</template>

<script>
import * as userService from '@/services/admin/userService'
import Card from '@/components/Card'
import DataTable from "@/components/DataTable";

export default {
  name: 'Users',
  components: {
    DataTable,
    Card,
  },
  data() {
    return {
      headers: [
        {
          key: 'id',
          name: 'ID',
          sortable: true,
        },
        {
          key: 'username',
          name: 'Username',
          default: true,
          sortable: true,
        },
        {
          key: 'name',
          name: 'Name',
          default: true,
        },
        {
          key: 'email',
          name: 'Email',
          default: true,
          sortable: true,
        },
        {
          key: 'role',
          name: 'Role',
          default: true,
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
      ]
    }
  },
  methods: {
    fetch({ query, page, perPage, sortBy, sortDesc }) {
      return userService.list({ query, page, perPage, sortBy, sortDesc }).then((res) => ({
        currentPage: res.current_page,
        lastPage: res.last_page,
        items: res.items,
        perPage,
        query,
        sortBy,
        sortDesc,
      }))
    },
  },
}
</script>
