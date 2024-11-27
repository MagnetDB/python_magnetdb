<template>
  <div class="mx-auto w-full max-w-lg">
    <div class="display-1 text-center mb-6">
      New material
    </div>

    <Card>
      <Form @submit="submit" @validate="validate">
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
            label="Nuance"
            name="nuance"
            type="text"
            :component="FormInput"
        />
        <FormField
            label="RPE"
            name="rpe"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: 'Pascal',
                  value: 'Pa',
                  symbol: 'Pa',
                },
                {
                  name: 'Mega Pascal',
                  value: 'MPa',
                  symbol: 'MPa',
                  default: true,
                },
                {
                  name: 'Bar',
                  value: 'bar',
                  symbol: 'bar',
                },
            ]"
            :required="true"
        />
        <FormField
            label="T Ref"
            name="t_ref"
            placeholder="20"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: 'Celsius',
                  value: 'celsius',
                  symbol: '°C',
                },
                {
                  name: 'Kelvin',
                  value: 'kelvin',
                  symbol: 'K',
                  default: true,
                }
            ]"
        />
        <FormField
            label="Volumic Mass"
            name="volumic_mass"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: 'kg/m^3',
                  value: 'kg/m^3',
                  symbol: 'kg/m³',
                  default: true,
                }
            ]"
        />
        <FormField
            label="Alpha"
            name="alpha"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: '1/Celsius',
                  value: 'celsius^-1',
                  symbol: '1/°C',
                },
                {
                  name: '1/Kelvin',
                  value: 'kelvin^-1',
                  symbol: '1/K',
                  default: true,
                }
            ]"
        />
        <FormField
            label="Specific Heat"
            name="specific_heat"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: 'J/K/kg',
                  value: 'J/K/kg',
                  symbol: 'J/K/kg',
                  default: true,
                }
            ]"
        />
        <FormField
            label="Electrical Conductivity"
            name="electrical_conductivity"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            target-unit="S"
            :unit-options="[
                {
                    name: '1/ohm/m',
                    value: 'S',
                    symbol: 'S',
                },
                {
                    name: '10^6/ohm/m',
                    value: 'MS',
                    symbol: 'MS',
                    default: true,
                },
            ]"
        />
        <FormField
            label="Thermal Conductivity"
            name="thermal_conductivity"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: 'W/m/K',
                  value: 'W/K/m',
                  symbol: 'W/K/m',
                  default: true,
                }
            ]"
        />
        <FormField
            label="Magnet Permeability"
            name="magnet_permeability"
            type="number"
            placeholder="0"
            :component="FormInput"
        />
        <FormField
            label="Young"
            name="young"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            target-unit="Pa"
            :unit-options="[
                {
                  name: 'Pascal',
                  value: 'Pa',
                  symbol: 'Pa',
                },
                {
                  name: 'Giga Pascal',
                  value: 'GPa',
                  symbol: 'GPa',
                  default: true,
                },
                {
                  name: 'Mega Pascal',
                  value: 'MPa',
                  symbol: 'MPa',
                },
                {
                  name: 'Bar',
                  value: 'bar',
                  symbol: 'bar',
                },
            ]"
        />
        <FormField
            label="Poisson"
            name="poisson"
            type="number"
            placeholder="0"
            :component="FormInput"
        />
        <FormField
            label="Expansion Coefficient"
            name="expansion_coefficient"
            type="number"
            placeholder="0"
            :component="FormInputWithUnit"
            :unit-options="[
                {
                  name: '1/Celsius',
                  value: 'celsius^-1',
                  symbol: '1/°C',
                },
                {
                  name: '1/Kelvin',
                  value: 'kelvin^-1',
                  symbol: '1/K',
                  default: true,
                }
            ]"
        />
        <Button type="submit" class="btn btn-primary">
          Save
        </Button>
      </Form>
    </Card>
  </div>
</template>

<script>
import * as Yup from 'yup'
import * as materialService from '@/services/materialService'
import Card from '@/components/Card'
import Form from "@/components/Form";
import FormField from "@/components/FormField";
import FormInput from "@/components/FormInput";
import FormInputWithUnit from "@/components/FormInputWithUnit";
import FormSelect from "@/components/FormSelect";
import FormUpload from "@/components/FormUpload";
import Button from "@/components/Button";

export default {
  name: 'MaterialNew',
  components: {
    Button,
    FormField,
    Form,
    Card,
  },
  data() {
    return {
      FormInput,
      FormInputWithUnit,
      FormSelect,
      FormUpload,
      error: null,
    }
  },
  methods: {
    submit(values, {setRootError}) {
      return materialService.create(values)
          .then((material) => {
            this.$router.push({ name: 'material', params: { id: material.id } })
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
