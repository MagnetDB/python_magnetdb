<template>
  <div v-if="!error">
    <div class="display-1 mb-6">
      My profile
    </div>

    <Card>
      <Form :initial-values="$store.state.user" @submit="submit" @validate="validate">
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
            :disabled="true"
            :default-value="$store.state.user.role"
        />
        <FormField
            label="API Key"
            name="api_key"
            type="text"
            :component="FormInput"
            :required="true"
            :disabled="true"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as Yup from "yup";
import * as userService from '@/services/userService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormSelect from "@/components/FormSelect";
import Button from "@/components/Button";

export default {
  name: 'Profile',
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
      config: null,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return userService.update({ name: values.name })
          .then((user) => {
            this.$store.commit('setUser', user)
          })
          .catch(setRootError)
    },
    validate() {
      return Yup.object().shape({
        name: Yup.string().required(),
      })
    },
  },
}
</script>
