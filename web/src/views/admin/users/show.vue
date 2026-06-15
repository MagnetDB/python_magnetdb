<template>
  <div v-if="!error">
    <div class="display-1 mb-6">
      User: {{ user.name }}
    </div>

    <Card>
      <Form :initial-values="user" @submit="submit" @validate="validate">
        <FormField
            label="Username"
            name="username"
            type="text"
            :component="FormInput"
            :required="true"
            :disabled="true"
        />
        <FormField
            label="Email"
            name="email"
            type="text"
            :component="FormInput"
            :required="true"
            :disabled="true"
        />
        <FormField
            label="Name"
            name="name"
            type="text"
            :component="FormInput"
            :required="true"
        />
        <FormField
          label="Role"
          name="role"
          :component="FormSelect"
          :required="true"
          :clearable="false"
          :options="[
            {
              name: 'Guest',
              value: 'guest'
            },
            {
              name: 'User',
              value: 'user'
            },
            {
              name: 'Designer',
              value: 'designer'
            },
            {
              name: 'Admin',
              value: 'admin'
            },
          ]"
          :default-value="user.role"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>
  </div>
  <Alert v-else :error="error" class="alert alert-danger"/>
</template>

<script>
import { markRaw } from 'vue'
import * as Yup from "yup";
import * as userService from '@/services/admin/userService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";

export default {
  name: 'User',
  components: {
    Card,
    FormField,
    Form,
    Button,
  },
  data() {
    return {
      FormInput: markRaw(FormInput),
      FormSelect: markRaw(FormSelect),
      error: null,
      user: null,
      config: null,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return userService.update({id: this.user.id, name: values.name, role: values.role.value})
          .then((res) => {
            this.user = res
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
      })
    },
  },
  async mounted() {
    try {
      this.user = await userService.find({id: this.$route.params.id})
    } catch (error) {
      this.error = error
    }
  },
}
</script>
