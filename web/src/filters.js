export function datetime(date) {
  if (!date) return

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
  }).format(date instanceof Date ? date : new Date(date))
}

export function statusName(status) {
  return {
    in_stock: 'In stock',
    in_study: 'In study',
    in_operation: 'In operation',
    defunct: 'Defunct',
    pending: 'Pending',
    in_progress: 'In progress',
    done: 'Done',
    failed: 'Failed',
    scheduled: 'Scheduled',
  }[status]
}

export function roleName(role) {
  return {
    guest: 'Guest',
    user: 'User',
    designer: 'Designer',
    admin: 'Admin',
  }[role]
}
