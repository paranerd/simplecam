<template>
  <div class="table-responsive">
    <table class="records">
      <thead>
        <th>Filename</th>
        <th class="text-right">Actions</th>
      </thead>
      <tbody>
        <tr class="record" v-for="record in records" :key="record">
          <td>{{ record }}</td>
          <td class="text-right">
            <router-link :to="{ name: 'Recording', params: { id: record }}" class="btn btn-green" title="Play">
              <font-awesome-icon icon="play" />
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      records: [],
    };
  },
  async mounted() {
    try {
      const records = await fetch(process.env.VUE_APP_API_URL + "/records");

      this.records = await records.json();
    }
    catch (err) {
      console.error(err);
    }
  },
};

</script>

<style scoped>
.table-responsive {
  width: 100%;
  overflow-x: auto;
}

table {
  border-collapse: collapse;
  border: 1px solid #ddd;
  white-space: nowrap;
  width: 100%;
}

table tbody,
table thead {
  width: 100%;
}

table td,
table th {
  border-top: 1px solid #ddd;
}

td:first-child,
th:first-child {
  padding-left: 15px !important;
}

td:last-child,
th:last-child {
  padding-right: 15px !important;
}

th {
  height: 50px;
  text-align: left;
}

th.text-right,
td.text-right {
  text-align: right;
}

.records {
  width: 100%;
}

.record {
  height: 40px;
}

.records td,
.records th {
  padding: 5px;
}

tr:nth-child(even) {
  background: #fafafa;
}

tr:hover {
  background: #eee;
}

.btn {
  margin-left: 5px;
  height: 100%;
  border: none;
  border-radius: 2px;
  color: white;
  padding: 5px 15px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 1rem;
  cursor: pointer;
}

.btn-green {
  background-color: #4caf50;

}

.btn-green:hover {
  background-color: #409443;
}

.btn-blue {
  background: #39cccc;
}
</style>
