<script setup lang="ts">
import { defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'

import { createAdminUser, deleteAdminUser, fetchAdminUser, listAdminUsers, updateAdminUser, type AdminUserCreatePayload, type AdminUserUpdatePayload } from '../services/admin_users'
import type { UserRead } from '../services/auth'

const props = defineProps<{
  token: string | null
}>()

const users = ref<UserRead[]>([])
const loading = ref(false)
const saving = ref(false)
const deletingUserId = ref<number | null>(null)
const editingUserId = ref<number | null>(null)
const notice = ref('')
const error = ref('')

const form = reactive({
  username: '',
  password: '',
  email: '',
  status: 'active',
  roles: ['learner'],
})
const rolesText = ref('learner')
const SectionHeader = defineAsyncComponent(() => import('../components/SectionHeader.vue'))
const NoticeBanner = defineAsyncComponent(() => import('../components/NoticeBanner.vue'))
const AdminUsersList = defineAsyncComponent(() => import('../components/AdminUsersList.vue'))
const AdminUserForm = defineAsyncComponent(() => import('../components/AdminUserForm.vue'))

function resetMessages() {
  notice.value = ''
  error.value = ''
}

function setError(message: string) {
  error.value = message
  notice.value = ''
}

function setNotice(message: string) {
  notice.value = message
  error.value = ''
}

function resetForm() {
  editingUserId.value = null
  form.username = ''
  form.password = ''
  form.email = ''
  form.status = 'active'
  form.roles = ['learner']
  rolesText.value = 'learner'
}

function fillForm(user: UserRead) {
  editingUserId.value = user.id
  form.username = user.username
  form.password = ''
  form.email = user.email ?? ''
  form.status = user.status
  form.roles = [...user.roles]
  rolesText.value = user.roles.join(', ')
}

async function loadUsers() {
  if (!props.token) {
    users.value = []
    return
  }

  loading.value = true
  try {
    users.value = await listAdminUsers(props.token)
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function editUser(user: UserRead) {
  if (!props.token) {
    return
  }

  resetMessages()
  try {
    const detail = await fetchAdminUser(props.token, user.id)
    fillForm(detail)
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载用户详情失败')
  }
}

async function saveUser() {
  if (!props.token) {
    return
  }

  saving.value = true
  resetMessages()
  try {
    const roles = rolesText.value.split(',').map((role) => role.trim()).filter(Boolean)
    const payload: AdminUserCreatePayload = {
      username: form.username.trim(),
      password: form.password,
      email: form.email?.trim() || null,
      status: form.status || 'active',
      roles,
    }

    if (editingUserId.value === null) {
      await createAdminUser(props.token, payload)
      setNotice('已创建用户')
    } else {
      const updatePayload: AdminUserUpdatePayload = {
        username: payload.username,
        email: payload.email,
        status: payload.status,
        roles,
      }
      if (payload.password) {
        updatePayload.password = payload.password
      }
      await updateAdminUser(props.token, editingUserId.value, updatePayload)
      setNotice('已更新用户')
    }

    resetForm()
    await loadUsers()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存用户失败')
  } finally {
    saving.value = false
  }
}

async function removeUser(userId: number) {
  if (!props.token) {
    return
  }

  deletingUserId.value = userId
  resetMessages()
  try {
    await deleteAdminUser(props.token, userId)
    if (editingUserId.value === userId) {
      resetForm()
    }
    await loadUsers()
    setNotice('已删除用户')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除用户失败')
  } finally {
    deletingUserId.value = null
  }
}

watch(
  () => props.token,
  () => {
    resetMessages()
    resetForm()
    void loadUsers()
  },
  { immediate: true },
)

onMounted(() => {
  void loadUsers()
})
</script>

<script lang="ts">
export default {
  name: 'AdminUsersPage',
}
</script>

<template>
  <div class="page-card page-section">
    <SectionHeader kicker="管理员后台" title="用户管理" hint="支持列表、详情、创建、更新和删除" />

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <AdminUserForm
      :title="editingUserId ? '编辑用户' : '创建用户'"
      :username="form.username"
      :password="form.password"
      :email="form.email || ''"
      :status="form.status || 'active'"
      :roles-text="rolesText"
      :saving="saving"
      :submit-label="editingUserId ? '更新用户' : '创建用户'"
      reset-label="重置"
      @update:username="form.username = $event"
      @update:password="form.password = $event"
      @update:email="form.email = $event"
      @update:status="form.status = $event"
      @update:rolesText="rolesText = $event"
      @submit="saveUser"
      @reset="resetForm"
    />

    <section class="sub-card">
      <div class="section-header compact">
        <h3>用户列表</h3>
        <span class="workspace-hint" v-if="loading">加载中...</span>
      </div>

      <AdminUsersList :users="users" :loading="loading" :deleting-user-id="deletingUserId" @edit="editUser" @delete="removeUser" />
    </section>
  </div>
</template>
