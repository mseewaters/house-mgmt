<template>
  <div class="meals-view">
    <div class="placeholder-content">
      <h2>Meals</h2>
      <p>Meal tracking functionality will be implemented here</p>
      <div class="coming-soon">🍽️ Coming Soon</div>
    </div>
  </div>
</template>

<script setup>
// Placeholder component
</script>

<style scoped>
.meals-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.placeholder-content {
  text-align: center;
}

.placeholder-content h2 {
  font-family: var(--font-family-display);
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.placeholder-content p {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.coming-soon {
  font-size: 3rem;
  opacity: 0.3;
}
</style>