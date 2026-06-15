import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  ...pluginVue.configs['flat/essential'],
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
    },
  },
]
