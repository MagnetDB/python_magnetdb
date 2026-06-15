<template>
  <div id="app" class="mb-16">
    <div class="topbar"  :class="{ 'topbar-admin': isInAdminMode }">
      <div class="container-center">
        <div class="topbar-left">
          <router-link class="topbar-title" :to="{ name: 'home' }">
            MagnetDB
          </router-link>
          <div v-if="$store.getters.isLogged" class="topbar-link-list">
            <template v-if="isInAdminMode">
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'admin_config' }">
                Config
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'admin_users' }">
                Users
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'admin_audit_logs' }">
                Audit Logs
              </router-link>
            </template>
            <template v-else>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'sites' }">
                Sites
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'magnets' }">
                Magnets
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'parts' }">
                Parts
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'materials' }">
                Materials
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'records' }">
                Records
              </router-link>
              <router-link class="topbar-link" active-class="topbar-link-active" :to="{ name: 'simulations' }">
                Simulations
              </router-link>
            </template>
          </div>
        </div>
        <div v-if="$store.state.user" class="topbar-right topbar-dropdown" @click="dropdownActive = !dropdownActive">
          <span class="flex items-center cursor-pointer">
            Welcome, {{$store.state.user.name}}
            <ChevronDownIcon class="ml-1 h-5 w-5" />
          </span>
          <div v-if="dropdownActive" class="topbar-dropdown-content">
            <router-link class="topbar-dropdown-link" :to="{ name: 'profile' }">
              Profile
            </router-link>
            <router-link class="topbar-dropdown-link" :to="{ name: 'servers' }">
              Servers
            </router-link>
            <router-link
                v-if="$store.state.user.role === 'admin'"
                class="topbar-dropdown-link" :to="{ name: 'admin_config' }"
            >
              Administrate
            </router-link>
            <div class="topbar-dropdown-link topbar-dropdown-logout" @click="logout">
              Log out
            </div>
          </div>
        </div>
        <Button v-else class="btn btn-primary" @click="signIn">
          Sign In
        </Button>
      </div>
    </div>

    <div class="container-center">
      <router-view />
    </div>
  </div>
</template>

<script>
import { ChevronDownIcon } from '@heroicons/vue/24/solid'
import * as userService from '@/services/userService'
import Button from "@/components/Button.vue";
import * as sessionService from "@/services/sessionService";

export default {
  name: 'App',
  data() {
    return {
      dropdownActive: false,
    }
  },
  components: {
    Button,
    ChevronDownIcon,
  },
  watch: {
    '$store.getters.isLogged': {
      immediate: true,
      handler(logged) {
        if (!logged) return

        userService.find()
          .then((user) => this.$store.commit('setUser', user))
          .catch(console.error)
      },
    },
  },
  methods: {
    logout() {
      this.$store.commit('setToken', null)
      this.$router.push({ name: 'sign_in' })
    },
    async signIn() {
      this.error = null
      try {
        const res = await sessionService.getAuthorizationUrl({
          redirect_uri: `${window.location.origin}/sign_in`
        })
        window.location.href = res.url
      } catch (error) {
        this.error = error
      }
    },
  },
  computed: {
    isInAdminMode() {
      return this.$route.name?.startsWith('admin_')
    }
  }
}
</script>

<style scoped>
.topbar {
  @apply bg-white shadow-md mb-10;
}

.topbar > .container-center {
  @apply flex items-center justify-between;
}

.topbar-title,
.topbar-link {
  @apply h-16 flex items-center;
}

.topbar-title {
  @apply text-xl font-semibold text-blue-700 mr-8;
}

.topbar-left {
  @apply flex items-center;
}

.topbar-link-list {
  @apply flex items-center;
}

.topbar-link {
  @apply px-4 text-gray-700 font-medium;
}

.topbar-link-active {
  @apply bg-gray-100;
}

.topbar-dropdown {
  @apply relative;
}

.topbar-dropdown-content {
  @apply top-7 left-0 absolute w-64 bg-white border border-gray-100 shadow-md rounded-md flex flex-col z-10;
}

.topbar-dropdown-link {
  @apply text-gray-700 font-medium hover:bg-gray-100 py-2 px-3 cursor-pointer;
}

.topbar-dropdown-logout {
  @apply text-red-500 border-t border-gray-200;
}

.topbar-admin {
  @apply bg-red-100;
}

.topbar-admin .topbar-title {
  @apply text-red-700;
}

.topbar-admin .topbar-link-active {
  @apply bg-red-200;
}
</style>
