import { config } from '@vue/test-utils'

// Suppress Vue warnings for unresolved components in unit tests
config.global.stubs = {}
