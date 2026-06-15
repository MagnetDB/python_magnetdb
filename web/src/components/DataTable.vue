<template>
  <div>
    <div class="flex items-center space-x-4 mb-2">
      <FormInput type="text" :value="query" @value="search" placeholder="Search..." />
      <div class="columns-dropdown">
        <button
          class="btn btn-default flex items-center cursor-pointer"
          @click="columnsDropdownActive = !columnsDropdownActive"
        >
          Columns
          <ChevronDownIcon class="ml-1 h-5 w-5" />
        </button>
        <div v-if="columnsDropdownActive" class="columns-dropdown-content">
          <div v-for="header in headers" :key="header.key" class="columns-dropdown-item" @click="toggleColumn(header)">
            <input type="checkbox" :checked="isColumnEnabled(header)" />
            {{header.name}}
          </div>
        </div>
      </div>
    </div>

    <div class="table-responsive">
      <table class="mb-6">
        <thead class="bg-white">
          <tr>
            <th
              v-for="header in currentHeaders" :key="header.key" draggable="true"
              @dragstart="startMovingColumn(header, $event)" @drop="moveColumn(header, $event)"
              @dragover="$event.preventDefault()"
            >
              <div
                class="flex items-center" @click="toggleSort(header)" :class="{ 'cursor-pointer': header.sortable }"
                @mouseenter="headerMouseEnter(header)" @mouseleave="headerMouseLeave(header)"
              >
                {{ header.name }}
                <ArrowUpIcon
                  v-if="sortBy === header.key || currentHeaderHover === header.key"
                  class="ml-2 h-3 w-3 transform"
                  :class="{
                    'text-gray-600': !currentHeaderHover,
                    'text-gray-400': currentHeaderHover,
                    'rotate-180': sortDesc,
                  }"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody v-if="dataVisible">
          <tr
            v-for="item in items" :key="getItemKey(item)" class="hover:bg-gray-100"
            :class="{ 'cursor-pointer': $attrs.onItemSelected }" @click="$emit('item-selected', item)"
          >
            <td v-for="header in currentHeaders" :key="header.key">
              <slot v-if="$slots[`item.${header.key}`]" :name="`item.${header.key}`" :item="item" :items="items" />
              <template v-else>{{ item[header.key] }}</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="dataVisible" class="flex items-center justify-end space-x-4">
      <div class="flex items-center">
        <span class="mr-2">Rows per page:</span>
        <select class="form-input" @input="fetch({ perPage: $event.target.value })" :value="perPage">
          <option v-for="opt in rowsPerPageOptions" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </div>
      <div>Page {{ currentPage }} of {{ lastPage }}</div>
      <button
        class="rounded-full p-2" @click="previousPage"
        :class="{ 'hover:bg-gray-100': hasPreviousPage, 'text-gray-500': !hasPreviousPage }"
      >
        <ChevronLeftIcon class="h-6 w-6" />
      </button>
      <button
        class="rounded-full p-2" @click="nextPage"
        :class="{ 'hover:bg-gray-100': hasNextPage, 'text-gray-500': !hasNextPage }"
      >
        <ChevronRightIcon class="h-6 w-6" />
      </button>
    </div>

    <div v-if="isLoading" class="text-center mb-4">Loading data...</div>

    <Alert v-if="error" :error="error" class="alert alert-danger" />
  </div>
</template>

<script>
import { debounce, isEqual } from "lodash"
import { ChevronLeftIcon, ChevronRightIcon, ArrowUpIcon, ChevronDownIcon } from "@heroicons/vue/24/solid"
import Alert from "@/components/Alert"
import FormInput from "@/components/FormInput"

export default {
  name: 'DataTable',
  components: {
    FormInput,
    Alert,
    ChevronLeftIcon,
    ChevronRightIcon,
    ChevronDownIcon,
    ArrowUpIcon,
  },
  props: ['headers', 'itemKey', 'configPersistenceKey'],
  data() {
    return {
      currentHeaders: [],
      isLoading: true,
      error: null,
      items: [],
      perPage: 10,
      currentPage: 1,
      lastPage: 0,
      sortBy: null,
      sortDesc: null,
      query: '',
      currentHeaderHover: '',
      columnsDropdownActive: false,
      rowsPerPageOptions: [10, 25, 50, 75, 100],
    }
  },
  watch: {
    currentHeaders: {
      deep: true,
      handler(headers) {
        this.writeState({
          page: this.currentPage,
          perPage: this.perPage,
          sortBy: this.sortBy,
          sortDesc: this.sortDesc,
          query: this.query,
          headers,
        })
      },
    },
  },
  methods: {
    getItemKey(item) {
      return item[this.itemKey || 'id']
    },
    isColumnEnabled(header) {
      return this.currentHeaders.some((curr) => curr.key === header.key)
    },
    async fetch({
      page = this.currentPage, perPage = this.perPage,
      sortBy = this.sortBy, sortDesc = this.sortDesc,
      query = this.query,
    } = {}) {
      this.isLoading = true
      this.error = null
      try {
        const res = await this.$attrs.onFetch({ page, perPage, sortBy, sortDesc, query })
        this.items = res.items
        this.perPage = res.perPage
        this.currentPage = res.currentPage
        this.lastPage = res.lastPage
        this.sortBy = res.sortBy
        this.sortDesc = res.sortDesc
        this.query = res.query
        this.writeState({
          page, perPage, sortBy, sortDesc, query, headers: this.currentHeaders
        })
      } catch (error) {
        this.error = error
      } finally {
        this.isLoading = false
      }
    },
    previousPage() {
      if (!this.hasPreviousPage) {
        return
      }
      return this.fetch({ page: this.currentPage - 1 })
    },
    nextPage() {
      if (!this.hasNextPage) {
        return
      }
      return this.fetch({ page: this.currentPage + 1 })
    },
    headerMouseEnter(header) {
      if (!header.sortable) {
        return
      }
      this.currentHeaderHover = header.key
    },
    headerMouseLeave() {
      this.currentHeaderHover = ''
    },
    toggleSort(header) {
      if (!header.sortable) {
        return
      } else if (this.sortBy !== header.key) {
        return this.fetch({ sortBy: header.key, sortDesc: false })
      } else if (!this.sortDesc) {
        return this.fetch({ sortDesc: true })
      }
      return this.fetch({ sortBy: null, sortDesc: false })
    },
    toggleColumn(header) {
      if (this.isColumnEnabled(header)) {
        this.currentHeaders = this.currentHeaders.filter((curr) => curr.key !== header.key)
        return
      }
      this.currentHeaders = [...this.currentHeaders, header]
    },
    startMovingColumn(header, e) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', header.key)
    },
    moveColumn(header, e) {
      const fromKey = e.dataTransfer.getData('text/plain')
      const fromHeader = this.currentHeaders.find((curr) => curr.key === fromKey)
      const fromIndex = this.currentHeaders.indexOf(fromHeader)
      const toIndex = this.currentHeaders.indexOf(this.currentHeaders.find((curr) => curr.key === header.key))

      const currentHeaders = [...this.currentHeaders]
      currentHeaders.splice(fromIndex, 1)
      currentHeaders.splice(toIndex, 0, fromHeader)
      this.currentHeaders = currentHeaders
    },
    search: debounce(function (query) {
      this.fetch({ query, page: 1 })
    }, 2000),
    writeState({ page, perPage, sortBy, sortDesc, query, headers }) {
      const queryPayload = {}
      if (page !== 1) {
        queryPayload.page = page
      }
      if (perPage !== 10) {
        queryPayload.per_page = perPage
      }
      if (sortBy) {
        queryPayload.sort_by = sortBy
      }
      if (sortDesc) {
        queryPayload.sort_desc = sortDesc
      }
      if (query?.trim()) {
        queryPayload.query = query
      }
      if (!isEqual(
        this.headers.filter(header => header.default).map(header => header.key),
        headers.map(header => header.key)
      )) {
        queryPayload.headers = headers.map(header => header.key).join(',')
      }
      if (Object.entries(queryPayload).length > 0 || Object.entries(this.$route.query).length > 0) {
        this.$router.replace({ ...this.$route, query: queryPayload }).catch(() => {})
      }
      if (this.configPersistenceKey) {
        localStorage.setItem(`mdb-datatable-${this.configPersistenceKey}`, JSON.stringify({ ...queryPayload }))
      }
    },
  },
  computed: {
    dataVisible() {
      return !this.error && !this.isLoading
    },
    hasPreviousPage() {
      return this.currentPage > 1
    },
    hasNextPage() {
      return this.currentPage < this.lastPage
    },
  },
  created() {
    try {
      let rawDefaultParams = {}
      if (this.configPersistenceKey) {
        const persistedConfig = localStorage.getItem(`mdb-datatable-${this.configPersistenceKey}`)
        if (persistedConfig) {
          rawDefaultParams = { ...rawDefaultParams, ...JSON.parse(persistedConfig) }
        }
      }
      rawDefaultParams = { ...rawDefaultParams, ...this.$route.query }

      if (rawDefaultParams.page) {
        this.currentPage = parseInt(rawDefaultParams.page, 10)
      }
      if (rawDefaultParams.per_page) {
        this.perPage = parseInt(rawDefaultParams.per_page, 10)
      }
      if (rawDefaultParams.sort_by) {
        this.sortBy = rawDefaultParams.sort_by
      }
      if (rawDefaultParams.sort_desc) {
        this.sortDesc = true
      }
      if (rawDefaultParams.sort_desc) {
        this.sortDesc = true
      }
      if (rawDefaultParams.query) {
        this.query = rawDefaultParams.query
      }
      if (rawDefaultParams.headers) {
        this.currentHeaders = rawDefaultParams.headers.split(',').map(
          (key) => this.headers.find((header) => header.key === key.trim())
        )
      }
    } catch (error) {
      console.error(error)
    }

    if (this.currentHeaders.length === 0) {
      this.currentHeaders = this.headers.filter((header) => header.default)
    }
  },
  mounted() {
    return this.fetch()
  }
}
</script>

<style scoped>
.form-input {
  @apply focus:ring-blue-500 focus:border-blue-500 block shadow-sm sm:text-sm border-gray-300 rounded-md;
}

.columns-dropdown {
  @apply relative;
}

.columns-dropdown-content {
  @apply top-10 left-0 absolute w-64 bg-white border border-gray-100 shadow-md rounded-md flex flex-col;
}

.columns-dropdown-item {
  @apply flex items-center text-gray-700 font-medium hover:bg-gray-100 py-2 px-3 cursor-pointer;
}

.columns-dropdown-item > input {
  @apply rounded-md mr-2;
}
</style>
