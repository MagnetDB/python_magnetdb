<template>
  <div v-if="site">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-4">
        <div class="display-1">
          Site Definition: {{ site.name }}
        </div>
        <StatusBadge :status="site.status"></StatusBadge>
      </div>
      <div class="flex items-center space-x-4">
        <Button v-if="site.status === 'in_study'" class="btn btn-success" type="button" @click="putInOperation">
          Put in operation
        </Button>
        <Button v-else-if="site.status === 'in_operation'" class="btn btn-danger" type="button" @click="shutdown">
          Shutdown site
        </Button>

        <Popover>
          <Button class="btn btn-default">
            Visualize
          </Button>

          <template #content>
            <div class="space-y-2">
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_bmap', query: { resource_type: 'site', resource_id: site.id } }"
              >
                BMAP
              </router-link>
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_stress_map', query: { resource_type: 'site', resource_id: site.id } }"
              >
                Stress map
              </router-link>
              <router-link
                  class="btn btn-default btn-block"
                  :to="{ name: 'visualisation_bmap_2d', query: { resource_type: 'site', resource_id: site.id } }"
              >
                BMAP 2D
              </router-link>
            </div>
          </template>
        </Popover>
      </div>
    </div>

    <Alert v-if="error" class="alert alert-danger mb-6" :error="error"/>

    <Card class="mb-6">
      <template #header>
        Details
      </template>

      <Form :initial-values="site" @submit="submit" @validate="validate">
        <FormField
            label="Name"
            name="name"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
            label="Description"
            name="description"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="Config file"
            name="config"
            type="text"
            :component="FormUpload"
            :default-value="site.config"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>

    <Card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <div>Magnets</div>
          <Button
              v-if="site.status === 'in_study'"
              class="btn btn-primary btn-small"
              @click="attachMagnetModalVisible = true"
          >
            Add a magnet
          </Button>
        </div>
      </template>

      <div class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th class="whitespace-nowrap">Name</th>
              <th class="whitespace-nowrap">Description</th>
              <th class="whitespace-nowrap">Status</th>
              <th class="whitespace-nowrap">Z offset</th>
              <th class="whitespace-nowrap">R offset</th>
              <th class="whitespace-nowrap">Parallax</th>
              <th class="whitespace-nowrap"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="siteMagnet in site.site_magnets" :key="siteMagnet.id">
              <td class="whitespace-nowrap">
                <router-link :to="{ name: 'magnet', params: { id: siteMagnet.magnet.id } }" class="link">
                  {{ siteMagnet.magnet.name }}
                </router-link>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="siteMagnet.magnet.description">{{ siteMagnet.magnet.description }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
              <td class="whitespace-nowrap">
                <StatusBadge :status="siteMagnet.magnet.status"></StatusBadge>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="siteMagnet.z_offset !== null">{{ siteMagnet.z_offset }}</template>
                <span v-else class="text-gray-500 italic">Not set</span>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="siteMagnet.r_offset !== null">{{ siteMagnet.r_offset }}</template>
                <span v-else class="text-gray-500 italic">Not set</span>
              </td>
              <td class="whitespace-nowrap">
                <template v-if="siteMagnet.parallax !== null">{{ siteMagnet.parallax }}</template>
                <span v-else class="text-gray-500 italic">Not set</span>
              </td>
              <td class="whitespace-nowrap">
                <Button
                    v-if="['in_study', 'in_stock'].includes(site.status)"
                    class="btn btn-danger btn-small"
                    @click="removeMagnet(siteMagnet)"
                >
                  Remove magnet
                </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <Card>
      <template #header>
        <div>Records</div>
      </template>

      <div class="table-responsive">
        <table>
          <thead class="bg-white">
            <tr>
              <th>Name</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in site.records" :key="record.id">
              <td>
                <router-link :to="{ name: 'record', params: { id: record.id } }" class="link">
                  {{ record.name }}
                </router-link>
              </td>
              <td>
                <template v-if="record.description">{{ record.description }}</template>
                <span v-else class="text-gray-500 italic">Not available</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <AttachMagnetToSiteModal
      :site-id="site.id"
      :visible="attachMagnetModalVisible"
      @close="attachMagnetModalVisible = false; fetch()"
    />
  </div>
  <Alert v-else-if="error" class="alert alert-danger" :error="error"/>
</template>

<script>
import * as Yup from 'yup'
import * as siteService from '@/services/siteService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";
import Alert from "@/components/Alert";
import AttachMagnetToSiteModal from "@/views/sites/show/AttachMagnetToSiteModal";
import StatusBadge from "@/components/StatusBadge";
import Popover from "@/components/Popover";

export default {
  name: 'SiteShow',
  components: {
    Popover,
    StatusBadge,
    AttachMagnetToSiteModal,
    Alert,
    Button,
    FormField,
    Form,
    Card,
  },
  data() {
    return {
      FormInput,
      FormSelect,
      FormUpload,
      error: null,
      site: null,
      attachMagnetModalVisible: false,
    }
  },
  methods: {
    putInOperation() {
      return siteService.putInOperation({ siteId: this.site.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
    shutdown() {
      return siteService.shutdown({ siteId: this.site.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
    submit(values, {setRootError}) {
      const payload = {
        id: this.site.id,
        name: values.name,
        description: values.description,
      }
      if (values.config instanceof File) {
        payload.config = values.config
      }

      return siteService.update(payload)
          .then(this.fetch)
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
      })
    },
    fetch() {
      return siteService.find({id: this.$route.params.id})
          .then((site) => {
            this.site = site
          })
          .catch((error) => {
            this.error = error
          })
    },
    removeMagnet(siteMagnet) {
      siteService.deleteMagnet({ siteMagnetId: siteMagnet.id })
          .then(this.fetch)
          .catch((error) => {
            this.error = error
          })
    },
  },
  async mounted() {
    await this.fetch()
  },
}
</script>
