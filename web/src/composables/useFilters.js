import { datetime, statusName, roleName } from '@/filters'

export function useFilters() {
  return { datetime, statusName, roleName }
}
