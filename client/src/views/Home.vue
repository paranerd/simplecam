<template>
  <div class="home">
    <h1>SimpleCam</h1>

    <div class="links">
      <router-link to="live" class="btn">Live</router-link>
      <router-link to="archive" class="btn">Archive</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: "Home",
  created() {
    document.title = `Home | ${process.env.VUE_APP_APP_NAME}`;
  },
};
</script>

<style lang="scss" scoped>
.home {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.links {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.btn {
  border: none;
  border-radius: 2px;
  padding: 5px 15px;
  color: black;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 1rem;
  cursor: pointer;
}

.btn:hover {
  background: #001f3f;
  color: white;
}
</style>
