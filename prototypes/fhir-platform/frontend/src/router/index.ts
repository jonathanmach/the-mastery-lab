import { createRouter, createWebHistory } from 'vue-router'
import PatientListView from '../views/PatientListView.vue'
import PatientDetailView from '../views/PatientDetailView.vue'
import OmopChatView from '../views/OmopChatView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/patients' },
    { path: '/patients', component: PatientListView },
    { path: '/patients/:id', name: 'patient-detail', component: PatientDetailView, props: true },
    { path: '/omop', name: 'omop-chat', component: OmopChatView },
  ],
})
