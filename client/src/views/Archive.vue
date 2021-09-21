<template>
  <div class="archive">
    <h1>Archive</h1>

    <Records />
  </div>
</template>

<script>
import Records from "@/components/Records.vue";

export default {
  name: "Archive",
  components: {
    Records
  },
  created() {
    document.title = `Archive | ${process.env.VUE_APP_APP_NAME}`;
  },
}
</script>

<style lang="scss" scoped>
.archive {
  display: flex;
  justify-items: center;
  align-items: center;
  flex-direction: column;
}
</style>
