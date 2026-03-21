<template>
  <div id="layout">
    <header>
      <RouterLink to="/patients" class="brand">FHIR Platform</RouterLink>
    </header>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
#layout { display: flex; flex-direction: column; min-height: 100vh; }
header {
  background: #0d6efd;
  color: #fff;
  padding: 0 24px;
  height: 48px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.brand { color: #fff; font-weight: 700; font-size: 16px; letter-spacing: 0.5px; text-decoration: none; }
main { flex: 1; }
</style>
