<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import AppIcon from '@/shared/components/AppIcon.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { authStore } from '@/modules/auth/store'
import AdminUserForm from '../components/AdminUserForm.vue'
import AdminUsersList from '../components/AdminUsersList.vue'
import {
  createAdminUser,
  deleteAdminUser,
  fetchAdminUser,
  listAdminUsers,
  updateAdminUser,
  type AdminUserCreatePayload,
  type AdminUserUpdatePayload,
} from '../services/admin-users.service'

const users = ref([])
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

function resetMessages() { notice.value = ''; error.value = '' }
function setError(msg: string) { error.value = msg; notice.value = '' }
function setNotice(msg: string) { notice.value = msg; error.value = '' }

function resetForm() {
  editingUserId.value = null
  form.username = ''; form.password = ''; form.email = ''
  form.status = 'active'; form.roles = ['learner']; rolesText.value = 'learner'
}

function fillForm(user: { id: number; username: string; email: string | null; status: string; roles: string[] }) {
  editingUserId.value = user.id
  form.username = user.username; form.password = ''
  form.email = user.email ?? ''; form.status = user.status
  form.roles = [...user.roles]; rolesText.value = user.roles.join(', ')
}

async function loadUsers() {
  if (!authStore.token) return
  loading.value = true
  try { users.value = await listAdminUsers(authStore.token) }
  catch (err) { setError(err instanceof Error ? err.message : '加载用户列表失败') }
  finally { loading.value = false }
}

async function editUser(user: { id: number }) {
  if (!authStore.token) return
  resetMessages()
  try { const detail = await fetchAdminUser(authStore.token, user.id); fillForm(detail) }
  catch (err) { setError(err instanceof Error ? err.message : '加载用户详情失败') }
}

async function saveUser() {
  if (!authStore.token) return
  saving.value = true; resetMessages()
  try {
    const roles = rolesText.value.split(',').map((r) => r.trim()).filter(Boolean)
    const payload: AdminUserCreatePayload = { username: form.username.trim(), password: form.password, email: form.email?.trim() || null, status: form.status || 'active', roles }
    if (editingUserId.value === null) {
      await createAdminUser(authStore.token, payload); setNotice('已创建用户')
    } else {
      const updatePayload: AdminUserUpdatePayload = { username: payload.username, email: payload.email, status: payload.status, roles }
      if (payload.password) updatePayload.password = payload.password
      await updateAdminUser(authStore.token, editingUserId.value, updatePayload); setNotice('已更新用户')
    }
    resetForm(); await loadUsers()
  } catch (err) { setError(err instanceof Error ? err.message : '保存用户失败') }
  finally { saving.value = false }
}

async function removeUser(userId: number) {
  if (!authStore.token) return
  deletingUserId.value = userId; resetMessages()
  try { await deleteAdminUser(authStore.token, userId); if (editingUserId.value === userId) resetForm(); await loadUsers(); setNotice('已删除用户') }
  catch (err) { setError(err instanceof Error ? err.message : '删除用户失败') }
  finally { deletingUserId.value = null }
}

onMounted(() => { void loadUsers() })
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <div>
        <h1>用户管理</h1>
        <p>创建、编辑和维护用户状态</p>
      </div>
    </header>

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <div class="admin-grid">
      <!-- Form -->
      <div class="card">
        <div class="card-header">
          <h3>{{ editingUserId ? '编辑用户' : '创建用户' }}</h3>
          <button v-if="editingUserId" type="button" class="link-btn" @click="resetForm">取消</button>
        </div>
        <div class="card-body">
          <AdminUserForm
            :title="editingUserId ? '编辑用户' : '创建用户'"
            :username="form.username"
            :password="form.password"
            :email="form.email || ''"
            :status="form.status || 'active'"
            :roles-text="rolesText"
            :saving="saving"
            :submit-label="editingUserId ? '更新' : '创建'"
            reset-label="重置"
            @update:username="form.username = $event"
            @update:password="form.password = $event"
            @update:email="form.email = $event"
            @update:status="form.status = $event"
            @update:rolesText="rolesText = $event"
            @submit="saveUser"
            @reset="resetForm"
          />
        </div>
      </div>

      <!-- List -->
      <div class="card">
        <div class="card-header">
          <h3>用户列表</h3>
          <span v-if="loading" class="loading-text">加载中...</span>
        </div>
        <div class="card-body">
          <AdminUsersList :users="users" :loading="loading" :deleting-user-id="deletingUserId" @edit="editUser" @delete="removeUser" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.page-header h1 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0 0 4px; }
.page-header p { font-size: 13px; color: var(--muted); margin: 0; }

.admin-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
}

.card { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl); overflow: hidden; }
.card-header { padding: 16px 24px; border-bottom: 1px solid var(--line-soft); display: flex; align-items: center; justify-content: space-between; }
.card-header h3 { font-size: 14px; font-weight: 600; color: var(--ink); margin: 0; }
.card-body { padding: 24px; }

.link-btn { background: none; border: none; color: var(--muted); font-size: 12px; cursor: pointer; padding: 4px 8px; border-radius: var(--radius-md); transition: all var(--transition-fast); }
.link-btn:hover { color: var(--accent); background: var(--accent-soft); }

.loading-text { font-size: 12px; color: var(--support); }

@media (max-width: 900px) {
  .admin-grid { grid-template-columns: 1fr; }
}
</style>
