<template>
  <div class="nav-wrapper">
    <span><router-link to="/" class="home">SimpleCam</router-link></span>
    <div class="username">paranerd</div>
  </div>
</template>

<script>
export default {};
</script>

<style lang="scss" scoped>
.nav-wrapper {
  position: fixed;
  top: 0;
  width: 100%;
  height: 5rem;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  color: white;
  background: #BC243C;
  box-sizing: border-box;
}

.home {
  color: white;
}

.username {
  margin-left: auto;
}
</style>
