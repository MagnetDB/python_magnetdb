const globals = require('globals')
const js = require('@eslint/js')
const pluginVue = require('eslint-plugin-vue')
const babelParser = require('@babel/eslint-parser')

module.exports = [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...pluginVue.configs['flat/vue2-essential'],
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        parser: babelParser,
        requireConfigFile: false,
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-reserved-component-names': 'off',
      'vue/valid-v-slot': 'off',
    },
  },
]
