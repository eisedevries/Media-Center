<template>
  <div class="min-h-screen overflow-hidden relative">
     <!-- Backend connection error notification -->
    <transition name="fade">
      <div 
        v-if="!backendConnected" 
        class="fixed top-4 right-4 bg-red-600 text-white px-4 py-3 rounded-lg shadow-lg z-50 flex z-[9999] items-center"
      >
        <span class="material-symbols-rounded mr-2">error</span>
        <span>Backend disconnected. Trying to reconnect...</span>
      </div>
    </transition>
    <!-- Wrapper for background & main content -->
    <div>
      <!-- Animated Background Image -->
      <div class="background-container">
      <div 
        class="background-image animate-pan"
        style="background-image: url('/assets/backgrounds/background.jpg');"
      ></div>
    </div>
      

      <!-- Main Content -->
      <div class="relative pt-4 p-8">
        <div v-if="selectedMovie" class="fixed inset-0 backdrop-blur-md bg-black bg-opacity-30 z-30"></div>
        <div class="flex items-center justify-center mb-4">
          <img src="/public/favicon.png" alt="Logo" class="h-14 mr-3" />
          <h1 class="animate-text bg-gradient-to-r from-blue-100 via-purple-100 to-orange-100 bg-clip-text text-transparent text-[2.7rem] font-bold">Media Center</h1>
        </div>
        <!-- Centered container with full width -->
        <div class="mx-auto w-full">
          <!-- Search Bar and Sorting Options -->
          <div class="flex items-center justify-between mb-6 mx-auto max-w-3xl">
            <!-- Search Bar -->
            <div class="relative flex-grow mr-4">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <img 
                  src="/public/assets/icons/search.svg" 
                  alt="Search" 
                  class="w-5 h-5 text-white search-icon"
                />
              </div>
              <input 
                type="text" 
                v-model="searchTerm" 
                placeholder="Search by title, genre, director or actors" 
                class="w-full pl-10 pr-6 py-2 bg-gray-800 bg-opacity-60 text-white placeholder-gray-400 rounded-lg border border-gray-700 focus:outline-none"
              >
              <!-- Clear search button - using same style as information container close button -->
              <button 
                v-show="searchTerm" 
                @click="searchTerm = ''"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-300 hover:text-gray-100"
              >
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>


            <!-- Sort Button -->
            <div class="relative sort-menu-container mr-2">
              <button 
                @click="toggleSortMenu"
                class="flex items-center px-4 py-2 bg-gray-800 bg-opacity-60 backdrop-blur-sm text-white rounded-lg border border-gray-700 hover:bg-gray-700 transition duration-200"
              >
                <img 
                   src="/public/assets/icons/sort.svg" 
                   alt="Search" 
                   class="w-5 h-5 text-white sort-icon mr-2"
                 />
                <span>Sort</span>
              </button>
              
              <!-- Sort Dropdown Menu -->
              <div 
                v-if="showSortMenu" 
                class="absolute right-0 mt-2 w-48 bg-gray-800 bg-opacity-90 backdrop-blur-lg rounded-lg shadow-lg z-20 border border-gray-700 overflow-hidden"
              >
                <div class="p-2">
                  <!-- Sort Options -->
                  <button 
                    v-for="option in sortOptions" 
                    :key="option.value"
                    @click="setSortOption(option.value)"
                    class="flex items-center justify-between w-full text-left px-3 py-2 hover:bg-gray-700 rounded transition-colors"
                    :class="{'text-blue-400': sortBy === option.value, 'text-white': sortBy !== option.value}"
                  >
                    <span>{{ option.label }}</span>
                    <span v-if="sortBy === option.value">
                      <template v-if="option.value === 'type'">
                        {{ sortDirection === 'asc' ? 'Movies' : 'TV Series' }}
                      </template>
                      <span v-else class="material-symbols-rounded text-sm">
                        {{ sortDirection === 'asc' ? 'arrow_upward' : 'arrow_downward' }}
                      </span>
                    </span>
                  </button>
                </div>
                
                <!-- Direction Toggle -->
              </div>

            </div>
            <div class="relative sync-container mr-2">
              <button 
                @click="manualSync"
                :disabled="isManualSyncing"
                class="flex items-center px-4 py-2 bg-gray-800 bg-opacity-60 backdrop-blur-sm text-white rounded-lg border border-gray-700 hover:bg-gray-700 transition duration-200"
              >
                <img 
                  src="/public/assets/icons/sync.svg" 
                  alt="Sync" 
                  class="w-5 h-5 text-white sync-icon mr-2"
                  :class="{'animate-spin': isManualSyncing}"
                />
                <span>{{ isManualSyncing ? 'Syncing...' : 'Sync' }}</span>
              </button>
            </div>
            <!-- here we implement the recommendation functionality-->
            <div class="relative prompt-container">
              <button 
                @click="copyPrompt"
                class="flex items-center px-4 py-2 bg-gray-800 bg-opacity-60 backdrop-blur-sm text-white rounded-lg border border-gray-700 hover:bg-gray-700 transition duration-200"
              >
                <img 
                  src="/public/assets/icons/wand_stars.svg" 
                  alt="Stars" 
                  class="w-5 h-5 text-white sync-icon mr-2"
                />
                <span>Recommendation</span>
              </button>
            </div>
            <transition name="modal-overlay">
              <div
                v-if="showPromptPopup"
                class="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm z-40"
                @click.self="showPromptPopup = false"
              ></div>
            </transition>

            <transition name="modal-content">
              <div
                v-if="showPromptPopup"
                class="fixed inset-0 flex items-center justify-center z-50"
                @click.self="showPromptPopup = false"
              >
                <div
                  class="bg-gray-900 text-white p-6 rounded-lg shadow-lg max-w-lg w-full mx-4 relative"
                  @click.stop
                >
                  <button
                    @click="showPromptPopup = false"
                    class="absolute top-2 right-2 text-gray-300 hover:text-gray-100"
                  >
                    <span class="material-symbols-rounded">close</span>
                  </button>
                  
                  <h2 class="text-xl md:text-2xl font-bold mb-4">
                    Find a movie recommendation
                  </h2>
                  
                  <p class="text-gray-400 mb-4">
                    What kind of movie are you in the mood for?
                  </p>
                  
                  <div class="mb-4">
                    <input
                      type="text"
                      v-model="userRequest"
                      placeholder="e.g., a sci-fi movie with time travel"
                      class="w-full px-4 py-2 bg-gray-800 bg-opacity-60 text-white placeholder-gray-400 rounded-lg border border-gray-700 focus:outline-none"
                      @keyup.enter="submitPrompt"
                    />
                  </div>
                  
                  <div class="flex justify-end">
                    <button
                      @click="submitPrompt"
                      class="flex items-center px-6 py-2 text-white rounded-lg transition duration-200 normal-button"
                    >
                      Go
                    </button>
                  </div>
                </div>
              </div>
            </transition>
          </div>
          <!-- Main View Grid: auto-fill columns fill entire width -->
          <div v-if="filteredAndSortedMovies.length" class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));">
            <div v-for="item in filteredAndSortedMovies" :key="item.path" class="bg-gray-900 shadow-md rounded-lg overflow-hidden transform transition duration-300 hover:scale-105 hover:shadow-2xl cursor-pointer" @click="openInformationContainer(item)">
              <div class="relative w-full aspect-[2/3] bg-gray-800">
                <!-- For folders, show aggregated cover if available -->
                <template v-if="item.type === 'FOLDER' && item.displayPoster">
                  <template v-if="item.folderCoverType === 'single'">
                    <img
                      :src="item.displayPoster"
                      alt="Folder cover"
                      class="absolute inset-0 w-full h-full object-cover"
                    />
                  </template>
                  <template v-else-if="item.folderCoverType === 'grid'">
                    <div class="absolute inset-0 grid grid-cols-2 grid-rows-2 gap-0.5">
                      <div
                        v-for="(cover, index) in item.displayPoster"
                        :key="index"
                        class="w-full h-full"
                      >
                        <img
                          :src="cover"
                          alt="Folder cover"
                          class="w-full h-full object-cover"
                        />
                      </div>
                    </div>
                  </template>
                </template>
                <!-- For video items (or folders without aggregated cover) -->
                <template v-else-if="item.poster">
                  <img
                    :src="item.poster"
                    :alt="item.title || item.name"
                    class="absolute inset-0 w-full h-full object-cover"
                  />
                </template>
                <!-- Fallback icon -->
                <template v-else>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <span class="material-symbols-rounded text-gray-400 text-5xl">
                      {{ item.type === 'FOLDER' ? 'folder' : 'theaters' }}
                    </span>
                  </div>
                </template>
              </div>
              <!-- Shows Title - year in main grid view on home page -->
              <div class="p-2">
                <h2 class="text-md font-semibold mb-1 text-white">
                  {{ item.title || item.name }}
                </h2>
                <p class="text-sm text-gray-400">
                  <!-- For non-folders with episodes, show season/episode -->
                  <template v-if="item.episode != null">
                    {{ formatSeasonEpisode(item.season, item.episode) }}
                  </template>
                  <!-- For non-folders with season but no year -->
                  <template v-else-if="item.type !== 'FOLDER' && item.season != null && item.year == null">
                    {{ formatSeason(item.season) }}
                  </template>
                  <!-- For folders, prefer year if available -->
                  <template v-else-if="item.type === 'FOLDER' && item.year != null">
                    {{ formatYear(item.year) }}
                  </template>
                  <!-- Otherwise, show year -->
                  <template v-else>
                    {{ formatYear(item.year) }}
                  </template>
                </p>
              </div>
            </div>
          </div>
          <div v-else class="text-center text-white">
            <p>Nothing found...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Overlay; clicking outside calls handleOverlayClick -->
    <transition name="modal-overlay">
      <div
        v-if="selectedMovie"
        class="fixed inset-0 bg-black bg-opacity-40 z-40 transition-all"
        @click.self="handleOverlayClick"
      ></div>
    </transition>

    <!-- Modal Content -->
    <transition name="modal-content">
      <div
        v-if="selectedMovie"
        class="fixed inset-0 flex items-center justify-center z-50 transition-all"
        @click.self="handleOverlayClick"
      >
        <div
          id="information-container"
          class="bg-gray-900 text-white p-6 rounded-lg shadow-lg max-w-6xl w-full mx-4 relative"
          @click.stop
        >
          <button
            @click="handleDeleteClick"
            class="absolute top-2 right-12 text-gray-300 hover:text-red-400 flex items-center"
            title="Delete"
          >
            <span class="material-symbols-rounded">delete</span>
          </button>
          <button
            @click="closeInformationContainer"
            class="absolute top-2 right-2 text-gray-300 hover:text-gray-100"
          >
            <span class="material-symbols-rounded">close</span>
          </button>

          <div class="content-switch-container">
            <transition name="modal-overlay" mode="out-in" duration="200">
              <!-- Folder (Container) View -->
              <div v-if="selectedMovie.type === 'FOLDER'" :key="'folder-'+selectedMovie.path">
                <div class="mb-4">
                  <!-- Big title; no path shown -->
                  <h2 class="text-3xl font-bold">
                    {{ selectedMovie.title || selectedMovie.name }}
                    <span v-if="isTrueSeasonFolder(selectedMovie)">
                      ‒ Season {{ selectedMovie.season }}
                    </span>
                    <span v-else-if="!selectedMovie.season && findCommonSeason(selectedMovie) !== null">
                      ‒ Season {{ findCommonSeason(selectedMovie) }}
                    </span>
                  </h2>
                </div>
                <!-- Container grid: 7 columns -->
                <div v-if="filteredChildren.length" class="grid gap-4" style="grid-template-columns: repeat(7, 1fr);">
                  <div v-for="child in filteredChildren" :key="child.path" class="bg-gray-800 shadow-md rounded-lg overflow-hidden transform transition duration-300 hover:scale-105 hover:shadow-2xl cursor-pointer" @click="openChild(child)">
                    <div class="relative w-full aspect-[2/3] bg-gray-700">
                      <template v-if="child.type === 'FOLDER' && child.displayPoster">
                        <template v-if="child.folderCoverType === 'single'">
                          <img
                            :src="child.displayPoster"
                            alt="Folder cover"
                            class="absolute inset-0 w-full h-full object-cover"
                          />
                        </template>
                        <template v-else-if="child.folderCoverType === 'grid'">
                          <div class="absolute inset-0 grid grid-cols-2 grid-rows-2 gap-0.5">
                            <div
                              v-for="(cover, index) in child.displayPoster"
                              :key="index"
                              class="w-full h-full"
                            >
                              <img
                                :src="cover"
                                alt="Folder cover"
                                class="w-full h-full object-cover"
                              />
                            </div>
                          </div>
                        </template>
                      </template>
                      <template v-else-if="child.poster">
                        <img
                          :src="child.poster"
                          :alt="child.title || child.name"
                          class="absolute inset-0 w-full h-full object-cover"
                        />
                      </template>
                      <template v-else>
                        <div class="absolute inset-0 flex items-center justify-center">
                          <span class="material-symbols-rounded text-gray-400 text-5xl">
                            {{ child.type === 'FOLDER' ? 'folder' : 'theaters' }}
                          </span>
                        </div>
                      </template>
                    </div>
                    <div class="p-2">
                      <!-- Show Season name or Episode name in folder grid view -->
                      <h2 class="text-md font-semibold mb-1 text-white">
                        <template v-if="child.type === 'FOLDER' && (isTrueSeasonFolder(child) || findCommonSeason(child) !== null)">
                          Season {{ child.season || findCommonSeason(child) }}
                        </template>
                        <template v-else-if="child.episode != null">
                          {{ child.episode_title || child.title || child.name }}
                        </template>
                        <template v-else>
                          {{ child.title || child.name }}
                        </template>
                      </h2>
                      <p class="text-sm text-gray-400">
                        <template v-if="child.episode != null">
                          {{ formatSeasonEpisode(child.season, child.episode) }}
                        </template>
                        <template v-else-if="child.type === 'FOLDER' && child.season === null">
                          <!-- we should not show S02 underneath Season 2 item title -->
                        </template>
                      </p>
                    </div>
                  </div>
                </div>
                <div v-else class="text-center text-gray-400">
                  <p>No items in this folder.</p>
                </div>
              </div>

              <!-- Movie/Video (OMDb) View -->
              <div v-else :key="'movie-'+selectedMovie.path">
                <div class="flex flex-col md:flex-row">
                  <div class="mb-4 md:mb-0 md:mr-4 flex-shrink-0 w-full md:w-1/3 cursor-pointer no-poster">
                    <template v-if="selectedMovie.poster">
                      <div class="relative" @click.stop="openVideoPopup">
                        <img
                          :src="selectedMovie.poster"
                          :alt="selectedMovie.title || selectedMovie.name"
                          class="w-full h-full object-cover rounded"
                        />
                        <span class="material-symbols-rounded absolute top-1/2 left-1/2 text-6xl cursor-pointer play-icon">
                          play_arrow
                        </span>
                      </div>
                    </template>
                    <template v-else>
                      <div
                        class="w-full h-full bg-gray-800 flex items-center justify-center rounded cursor-pointer"
                        @click.stop="openVideoPopup"
                      >
                        <span class="material-symbols-rounded text-gray-400 text-8xl cursor-pointer play-icon-no-poster">
                          play_arrow
                        </span>
                      </div>
                    </template>
                  </div>
                  <div class="flex-grow">
                    <template v-if="selectedMovie.episode != null">
                      <h2 class="text-xl md:text-2xl font-bold mb-2">
                        {{ selectedMovie.title || selectedMovie.name }} - {{ selectedMovie.episode_title }} 
                        <div class="text-gray-400 text-lg">
                          {{ formatSeasonEpisode(selectedMovie.season, selectedMovie.episode) }}
                        </div>
                        <template v-if="selectedMovie.duration"> - {{ selectedMovie.duration }}</template>
                      </h2>

                    </template>
                    <template v-else>
                      <h2 v-if="selectedMovie.duration" class="text-xl md:text-2xl font-bold mb-2">
                        {{ selectedMovie.title || selectedMovie.name }} ({{ formatYear(selectedMovie.year) }}) - {{ selectedMovie.duration }}
                      </h2>
                      <h2 v-else class="text-xl md:text-2xl font-bold mb-2">
                        {{ selectedMovie.title || selectedMovie.name }} ({{ formatYear(selectedMovie.year) }})
                      </h2>
                    </template>
                    <p v-if="selectedMovie.genre" class="text-sm text-gray-400 mb-1">
                      Genre: {{ selectedMovie.genre }}
                    </p>
                    <p v-if="selectedMovie.director" class="text-sm text-gray-400 mb-1">
                      Director: {{ selectedMovie.director }}
                    </p>
                    <p v-if="selectedMovie.actors" class="text-sm text-gray-400 mb-1">
                      Actors: {{ selectedMovie.actors }}
                    </p>
                    <p v-if="selectedMovie.language" class="text-sm text-gray-400 mb-1">
                      Language: {{ selectedMovie.language }}
                    </p>
                    <p v-if="selectedMovie.type" class="text-sm text-gray-400 mb-1">
                      Type: {{ getItemType(selectedMovie) }}
                    </p>
                    <br />
                    <p v-if="selectedMovie.plot" class="text-sm text-gray-400 mb-1">
                      {{ selectedMovie.plot }}
                    </p>
                    <br />
                    <a
                      v-if="selectedMovie.imdbVotes"
                      :href="`https://www.imdb.com/title/${selectedMovie.imdbID}/`"
                      target="_blank"
                      class="text-[#f3ce13] hover:underline"
                    >
                      IMDb: {{ selectedMovie.imdb }} - {{ selectedMovie.imdbVotes }} votes
                    </a>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </transition>

    <!-- Video Popup Modal -->
    <transition name="video">
      <div
        v-if="showVideoPopup"
        class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-85 backdrop-blur-md video-popup"
        @click.self="closeVideoPopup"
      >
        <div class="bg-transparent text-white p-1 rounded shadow text-center text-center">
          <p class="text-4xl mb-[16px]">
            Now playing
          </p>
          <p v-if="selectedMovie.episode != null" class="text-5xl mb-1">
            <b>
              {{ selectedMovie.title || selectedMovie.name }} - {{selectedMovie.episode_title }}
              <br>
            </b>
          </p>
          <p v-if="selectedMovie.episode != null" class="text-4xl mt-2">
              {{ formatSeasonEpisode(selectedMovie.season, selectedMovie.episode) }}
          </p>
          <p v-if="selectedMovie.episode == null" class="text-5xl mb-1">
            <b>{{ selectedMovie.title }}</b>
          </p>
        </div>
      </div>
    </transition>
  </div>

  <!-- Delete Confirmation Popup removed for minimal implementation -->

  <!-- Sync Success Notification -->
  <transition name="fade">
    <div 
      v-if="syncSuccessVisible"
      class="fixed top-4 right-4 bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg z-[99999] flex items-center"
    >
      <span class="material-symbols-rounded mr-2">check_circle</span>
      <span>Sync successful</span>
      <button @click="syncSuccessVisible = false" class="ml-4 text-white hover:text-gray-200">
        <span class="material-symbols-rounded">close</span>
      </button>
    </div>
  </transition>

  <!-- Delete Error Notification -->
  <transition name="fade">
    <div 
      v-if="deleteError"
      class="fixed top-4 right-4 bg-red-600 text-white px-4 py-3 rounded-lg shadow-lg z-[99999] flex items-center"
    >
      <span class="material-symbols-rounded mr-2">error</span>
      <span>{{ deleteError }}</span>
      <button @click="deleteError = ''" class="ml-4 text-white hover:text-gray-200">
        <span class="material-symbols-rounded">close</span>
      </button>
    </div>
  </transition>

</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import '~/assets/css/style.css'

// Fetch movies from the backend API (this call happens only once)
const { data: movies, error } = await useFetch('http://127.0.0.1:50005/api/movies')
if (error.value) {
  console.error('Error fetching movies:', error.value)
}
const prefix = "/remote.php/webdav/media/"; // define prefix at the top

// Recursive helper to find a folder by its relative path.
const findFolderByPath = (items, targetPath) => {
  for (const item of items) {
    if (item.type === 'FOLDER') {
      let folderPath = item.path;
      if (folderPath.startsWith(prefix)) {
        folderPath = folderPath.substring(prefix.length);
      }
      folderPath = folderPath.replace(/\/$/, ""); // remove trailing slash
      if (folderPath === targetPath) {
        return item;
      }
      if (item.children && item.children.length) {
        const found = findFolderByPath(item.children, targetPath);
        if (found) return found;
      }
    }
  }
  return null;
}

// Search and sorting functionality
const searchTerm = ref('')
const sortBy = ref('title')
const sortDirection = ref('asc')
const showSortMenu = ref(false)

const sortOptions = [
  { label: 'Title', value: 'title' },
  { label: 'Year', value: 'year' },
  { label: 'Duration', value: 'duration' },
  { label: 'IMDb Rating', value: 'imdb' },
  { label: 'IMDb Vote Count', value: 'imdbVotes' },
  { label: 'Type', value: 'type' }
]

const toggleSortMenu = () => {
  showSortMenu.value = !showSortMenu.value
}

const setSortOption = (option) => {
  // If clicking the same option, toggle direction instead
  if (sortBy.value === option) {
    toggleSortDirection()
  } else {
    sortBy.value = option
  }
}

const toggleSortDirection = () => {
  sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
}

// Close sort menu when clicking outside
const closeMenuOnOutsideClick = (event) => {
  if (showSortMenu.value && !event.target.closest('.sort-menu-container')) {
    showSortMenu.value = false
  }
}

// Add and remove event listener when showSortMenu changes
watch(showSortMenu, (isShown) => {
  if (isShown) {
    document.addEventListener('click', closeMenuOnOutsideClick)
  } else {
    document.removeEventListener('click', closeMenuOnOutsideClick)
  }
})

// Helper function to recursively get all video files from a folder and its subfolders
const getAllVideoFiles = (item) => {
  if (!item.children) return [];
  
  let videoFiles = [];
  
  for (const child of item.children) {
    if (child.type === 'FOLDER') {
      // Recursively get video files from subfolders
      videoFiles = videoFiles.concat(getAllVideoFiles(child));
    } else if (child['file-type'] === 'VIDEO') {
      // Add video file to the list
      videoFiles.push(child);
    }
  }
  
  return videoFiles;
};

// Helper function to determine if an item is a TV series
const isTVSeries = (item) => {
  // For individual items, check if they have season/episode properties
  if (item.type !== 'FOLDER') {
    return item.season != null && item.episode != null;
  }
  
  // For folders, check recursively
  if (item.children && item.children.length > 0) {
    // Get all video files in this folder and its subfolders
    const allVideoFiles = getAllVideoFiles(item);
    
    // If there are no video files, it's not a TV series
    if (allVideoFiles.length === 0) return false;
    
    // Check if ALL video files have season and episode
    return allVideoFiles.every(videoFile => 
      videoFile.season != null && videoFile.episode != null
    );
  }
  
  return false;
};

// Helper function to get comparable value for sorting
const getSortableValue = (item, sortKey) => {
  if (sortKey === 'title') {
    return (item.title || item.name || '').toLowerCase()
  } else if (sortKey === 'year') {
    // Items without a year will be placed at the bottom
    if (item.year == null) {
      return sortDirection.value === 'asc' ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER
    }
    return Array.isArray(item.year) ? item.year[0] : item.year
  } else if (sortKey === 'imdb') {
    // Items without an IMDB rating will be placed at the bottom
    if (!item.imdb) {
      return sortDirection.value === 'asc' ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER
    }
    return parseFloat(item.imdb)
  } else if (sortKey === 'imdbVotes') {
    // Items without votes will be placed at the bottom
    if (!item.imdbVotes) {
      return sortDirection.value === 'asc' ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER
    }
    // Parse vote count - handle formats like "911K", "1.2M", etc.
    return parseVoteCount(item.imdbVotes)
  } else if (sortKey === 'duration') {
    // Items without a duration will be placed at the bottom
    if (!item.duration) {
      return sortDirection.value === 'asc' ? Number.MAX_SAFE_INTEGER : Number.MIN_SAFE_INTEGER
    }
    
    // Parse duration - handle formats like "1h 45m", "125 min", etc.
    return parseDurationToMinutes(item.duration)
  } else if (sortKey === 'type') {
    return getItemType(item).toLowerCase()
  }
  return ''
}

// Add this function to parse vote counts
const parseVoteCount = (voteStr) => {
  if (!voteStr) return 0
  
  // Remove commas and other non-numerical characters except K, M, B
  const cleanStr = voteStr.replace(/[,\s]/g, '')
  
  // Parse the number part
  const numMatch = cleanStr.match(/^(\d+\.?\d*)/)
  if (!numMatch) return 0
  
  const num = parseFloat(numMatch[1])
  
  // Apply multiplier based on suffix
  if (cleanStr.endsWith('K')) {
    return num * 1000
  } else if (cleanStr.endsWith('M')) {
    return num * 1000000
  }
  
  return Number(num)
}


// Helper function to get item type display value
const getItemType = (item) => {
  if (isTVSeries(item)) {
    return "TV Series"
  }
  return "Movie"
}

// Helper function to parse duration strings to minutes
const parseDurationToMinutes = (durationStr) => {
  if (!durationStr) return 0
  
  let totalMinutes = 0
  
  // Handle formats like "1h 30m" or "1h30m"
  const hourMatch = durationStr.match(/(\d+)\s*h/i)
  if (hourMatch) {
    totalMinutes += parseInt(hourMatch[1], 10) * 60
  }
  
  // Handle minutes - either after hours or standalone like "45m" or "45 min"
  const minMatch = durationStr.match(/(\d+)\s*m/i)
  if (minMatch) {
    totalMinutes += parseInt(minMatch[1], 10)
  } else {
    // Try to match standalone minutes like "120 min"
    const standaloneMin = durationStr.match(/(\d+)\s*min/i)
    if (standaloneMin) {
      totalMinutes += parseInt(standaloneMin[1], 10)
    }
  }
  
  // If nothing matched but there's a number, assume it's minutes
  if (totalMinutes === 0) {
    const justNumber = durationStr.match(/(\d+)/)
    if (justNumber) {
      totalMinutes = parseInt(justNumber[1], 10)
    }
  }
  
  return totalMinutes
}



// Helper function to normalize text (remove accents/diacritics)
const normalizeText = (text) => {
  if (!text) return '';
  return text
    .normalize('NFD')                 // Decompose accented characters
    .replace(/[\u0300-\u036f]/g, ''); // Remove diacritical marks
}

// Flatten all video items recursively into a single array
const allVideoItems = computed(() => {
  const result = [];
  
  // Recursive function to collect all video items
  const collectVideoItems = (items, breadcrumbs = []) => {
    if (!items) return;
    
    items.forEach(item => {
      // Enhanced item with breadcrumb path for navigation
      const enhancedItem = { ...item, breadcrumbs: [...breadcrumbs] };
      
      if (item.type === 'FOLDER') {
        if (item.children) {
          // Add this folder to breadcrumbs for children
          collectVideoItems(item.children, [...breadcrumbs, item]);
        }
      } else if (item['file-type'] === 'VIDEO') {
        // Add video file to results
        result.push(enhancedItem);
      }
    });
  };
  
  // Start collection from processed movies
  collectVideoItems(processedMovies.value);
  return result;
});


// Filtered and sorted movies (single implementation)
const filteredAndSortedMovies = computed(() => {
  // Start with all video items when searching, otherwise use top-level items
  let result = searchTerm.value ? allVideoItems.value : videoMovies.value;
  
  // Filter by search term
  if (searchTerm.value) {
  const search = normalizeText(searchTerm.value.toLowerCase());
  result = result.filter(item => {
    // For TV episodes (items with season and episode numbers), only search the episode title
    if (item.season != null && item.episode != null) {
      const episodeTitle = normalizeText((item.episode_title || '').toLowerCase());
      return episodeTitle.includes(search);
    }
    
    // For movies and folders, search all relevant fields
    const title = normalizeText((item.title || item.name || '').toLowerCase());
    const genre = normalizeText((item.genre || '').toLowerCase());
    const director = normalizeText((item.director || '').toLowerCase());
    const actors = normalizeText((item.actors || '').toLowerCase());
    
    return title.includes(search) || 
           genre.includes(search) || 
           director.includes(search) || 
           actors.includes(search);
    });
  }
  
  // Sort by selected option
  result = [...result].sort((a, b) => {
    const aVal = getSortableValue(a, sortBy.value);
    const bVal = getSortableValue(b, sortBy.value);
    
    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1;
    return 0;
  });
  
  return result;
});
/**
 * Recursively process an item.
 * Returns a new object (without mutating the original).
 * For folders:
 *   - Recursively process children.
 *   - If no subfolder exists and exactly one VIDEO file is found (ignoring non‑video files),
 *     return that video item (flattening the folder).
 *   - Otherwise, compute an aggregated cover from all descendant video posters.
 */
function processItem(item) {
  const newItem = { ...item }

  if (newItem.type === 'FOLDER' && Array.isArray(newItem.children)) {
    newItem.children = newItem.children.map(child => processItem(child))
    const hasSubfolder = newItem.children.some(child => child.type === 'FOLDER')
    const immediateVideoChildren = newItem.children.filter(child => child['file-type'] === 'VIDEO')

    // Flatten if no subfolder exists and exactly one video file is found (ignoring non‑video files)
    if (!hasSubfolder && immediateVideoChildren.length === 1) {
      return immediateVideoChildren[0]
    }

    // Recursively collect all descendant video posters
    const descendantPosters = getDescendantPosters(newItem)
    const uniquePosters = []
    descendantPosters.forEach(p => {
      if (!uniquePosters.includes(p)) {
        uniquePosters.push(p)
      }
    })
    if (uniquePosters.length === 1) {
      newItem.folderCoverType = 'single'
      newItem.displayPoster = uniquePosters[0]
    } else if (uniquePosters.length > 1) {
      newItem.folderCoverType = 'grid'
      newItem.displayPoster = uniquePosters.slice(0, 4)
    }
  }
  return newItem
}

// Add this function to your <script setup> section
const isTrueSeasonFolder = (item) => {
  // The item has a season number but no episode number
  if (item.season != null && item.episode == null) {
    // Check if children exist and at least one has an episode number from this season
    if (item.children && item.children.length) {
      return item.children.some(child => 
        child.season === item.season && child.episode != null
      )
    }
    // Or if the folder name itself suggests it's a season
    const name = (item.title || item.name || '').toLowerCase()
    return name.includes('season ' + item.season) || 
           name.includes('s' + padNumber(item.season)) ||
           name === 'season ' + item.season
  }
  return false
}

/**
 * Recursively gathers descendant video posters from an item.
 */
function getDescendantPosters(item) {
  let posters = []
  if (item.type !== 'FOLDER') {
    if (item['file-type'] === 'VIDEO' && item.poster) {
      posters.push(item.poster)
    }
  } else if (item.children && Array.isArray(item.children)) {
    item.children.forEach(child => {
      posters = posters.concat(getDescendantPosters(child))
    })
  }
  return posters
}

// Process the API response once when movies are available.
const processedMovies = ref([])
watch(movies, (newVal) => {
  if (newVal) {
    processedMovies.value = newVal.map(item => processItem(item))
  }
}, { immediate: true })

// Helper functions for formatting
const padNumber = (num) => (num < 10 ? '0' + num : num.toString())
const formatYear = (year) => (Array.isArray(year) ? year.join(' - ') : year)
const formatSeason = (season) => (season != null ? `S${padNumber(season)}` : '')
const formatSeasonEpisode = (season, episode) => {
  if (season != null && episode != null) {
    return `S${padNumber(season)}E${padNumber(episode)}`
  }
  return ''
}

const deleteError = ref('')

// Store the currently selected item (movie or folder) and video popup flag.
const selectedMovie = ref(null)
const showVideoPopup = ref(false)

// Folder navigation history (for "Back" navigation).
const folderHistory = ref([])

// Toggle body scrolling when the modal is open.
watch(selectedMovie, (newVal) => {
  document.body.style.overflow = newVal ? 'hidden' : 'auto'
})

// Open the modal from the main grid; clear folder history on new open.
const openInformationContainer = (item) => {
  // If the item has breadcrumbs (it's nested), navigate through them
  if (item.breadcrumbs && item.breadcrumbs.length > 0) {
    // Clear folder history first
    folderHistory.value = [];
    
    // Navigate through breadcrumbs
    let currentItem = null;
    
    // Build folder history in reverse order
    for (let i = 0; i < item.breadcrumbs.length; i++) {
      const breadcrumb = item.breadcrumbs[i];
      if (i === 0) {
        // First breadcrumb is the root folder
        currentItem = breadcrumb;
      } else {
        // Push the previous item to history and navigate to next
        folderHistory.value.push(currentItem);
        currentItem = breadcrumb;
      }
    }
    
    // Finally, push the last folder to history and select the target item
    if (currentItem) {
      folderHistory.value.push(currentItem);
    }
    selectedMovie.value = item;
  } else {
    // Original behavior for top-level items
    folderHistory.value = [];
    selectedMovie.value = item;
  }
};

// Close the modal and clear folder history.
const closeInformationContainer = () => {
  selectedMovie.value = null
  folderHistory.value = []
}

// When a child item is clicked in a folder view, push the current folder (parent)
// onto the history regardless of whether the child is a folder or not.
const openChild = (child) => {
  folderHistory.value.push(selectedMovie.value)
  selectedMovie.value = child
}

// Navigate back to the previous folder.
const goBack = () => {
  if (folderHistory.value.length) {
    selectedMovie.value = folderHistory.value.pop()
  }
}

// Handle clicks on the overlay.
// If in a subfolder (folderHistory non-empty), go one level up.
// Otherwise, close the modal (return to main view).
const handleOverlayClick = () => {
  if (folderHistory.value.length) {
    selectedMovie.value = folderHistory.value.pop()
  } else {
    closeInformationContainer()
  }
}

const openVideoPopup = async () => {
  showVideoPopup.value = true;

  let subs = [];
  // Get the selected video's full path.
  const fullPath = selectedMovie.value.path; // e.g. "/remote.php/webdav/media/FolderName/filename.mkv"
  // Remove the prefix to get the relative path.
  let relativePath = fullPath.startsWith(prefix) ? fullPath.substring(prefix.length) : fullPath;
  // Extract the parent folder (everything before the last slash)
  const parentFolder = relativePath.substring(0, relativePath.lastIndexOf("/"));
  
  // Use the recursive helper to search in movies.value
  if (movies.value && Array.isArray(movies.value)) {
    const folderItem = findFolderByPath(movies.value, parentFolder);
    if (folderItem && folderItem.children) {
      const subtitleFiles = folderItem.children.filter(child => child["file-type"] === "SUBTITLE");
      if (selectedMovie.value.season != null && selectedMovie.value.episode != null) {
        // Only include subtitles that match the selected video's season and episode
        subs = subtitleFiles
          .filter(child => child.season === selectedMovie.value.season && child.episode === selectedMovie.value.episode)
          .map(child => "https://eisedv.stackstorage.com" + child.path);
      } else {
        // Fallback: include all subtitles (if season/episode info is missing)
        subs = subtitleFiles.map(child => "https://eisedv.stackstorage.com" + child.path);
      }
    }
  }

  let title;
  if (selectedMovie.value.episode != null) {
    title = `${selectedMovie.value.title || selectedMovie.value.name} - ${selectedMovie.value.episode_title} (${formatSeasonEpisode(selectedMovie.value.season, selectedMovie.value.episode)})`;
  } else {
    title = selectedMovie.value.title || selectedMovie.value.name;
  }

  // Prepare data for the playback request, including subtitle URLs if any.
  const playbackData = {
    path: selectedMovie.value.path,
    title: title,
    subs: subs
  };

  try {
    const response = await fetch('http://127.0.0.1:50005/api/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(playbackData)
    });
    const result = await response.json();
    if (!response.ok) {
      console.error('Error playing video:', result.error);
    }
  } catch (error) {
    console.error('Failed to send playback request:', error);
  }
}

const closeVideoPopup = () => {
  showVideoPopup.value = false
}

// --- WebSocket Connection ---
// This connection listens for the "close_video_popup" message to auto-close the video modal.
const ws = new WebSocket("ws://127.0.0.1:50005/ws")

ws.onopen = () => {
  console.log("WebSocket connection established")
}

ws.onmessage = (event) => {
  if (event.data === "close_video_popup") {
    closeVideoPopup()
  }
}

ws.onerror = (error) => {
  console.error("WebSocket error:", error)
}


const videoMovies = computed(() => {
  return processedMovies.value.filter(item => {
    // Always include folders
    if (item.type === 'FOLDER') {
      return true
    }
    // For individual items, include only those with a VIDEO file-type
    return item['file-type'] === 'VIDEO'
  })
})

// This computed property filters children in folder view (if available)
const filteredChildren = computed(() => {
  if (selectedMovie.value && selectedMovie.value.children) {
    return selectedMovie.value.children.filter(child => {
      return child.type === 'FOLDER' || child['file-type'] === 'VIDEO'
    })
  }
  return []
})

// Helper function to find a common season across all video files in a folder
const findCommonSeason = (item) => {
  if (!item.children) return null;
  
  // Get all video files in this folder and its subfolders
  const videoFiles = getAllVideoFiles(item);
  
  // If there are no video files, return null
  if (videoFiles.length === 0) return null;
  
  // Get the first video file with a season
  const firstVideoWithSeason = videoFiles.find(file => file.season != null);
  
  // If no video has a season, return null
  if (!firstVideoWithSeason) return null;
  
  const firstSeason = firstVideoWithSeason.season;
  
  // Check if all video files with seasons have the same season number
  const allSameSeason = videoFiles.every(file => 
    file.season == null || file.season === firstSeason
  );
  
  return allSameSeason ? firstSeason : null;
};

// Function to handle manual sync
const isManualSyncing = ref(false)

const syncSuccessVisible = ref(false)
let syncSuccessTimeout = null

const manualSync = async () => {
  try {
    isManualSyncing.value = true;
    // During sync, check backend connection only every minute
    if (connectionCheckInterval.value) clearInterval(connectionCheckInterval.value);
    connectionCheckInterval.value = setInterval(checkBackendConnection, 60000);

    const response = await fetch('http://127.0.0.1:50005/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error('Sync failed');
    }

    // Refresh movies after sync
    // Use $fetch instead of useFetch to avoid Nuxt warning
    try {
      const refreshedMovies = await $fetch('http://127.0.0.1:50005/api/movies');
      if (refreshedMovies) {
        movies.value = refreshedMovies;
      }
    } catch (fetchError) {
      console.error('Error fetching movies after sync:', fetchError);
    }

    // Show green sync success popup
    syncSuccessVisible.value = true;
    if (typeof syncSuccessTimeout !== "undefined" && syncSuccessTimeout) clearTimeout(syncSuccessTimeout);
    syncSuccessTimeout = setTimeout(() => {
      syncSuccessVisible.value = false;
    }, 4000);

  } catch (error) {
    console.error('Error during manual sync:', error);
    alert('Sync failed. Please check the console for details.');
  } finally {
    isManualSyncing.value = false;
    // After sync, reset backend connection check to every 5 seconds
    if (connectionCheckInterval.value) clearInterval(connectionCheckInterval.value);
    connectionCheckInterval.value = setInterval(checkBackendConnection, 5000);
  }
}

const showPromptPopup = ref(false)
const userRequest = ref('')

const copyPrompt = () => {
  // Clear previous input and show popup
  userRequest.value = ''
  showPromptPopup.value = true
}

const submitPrompt = () => {
  // Create the prompt text
  let promptText = `You are a movie recommendation agent. Your goal is in helping the user find a movie (or single tv show episode) to watch. Give around 5 - 10 items unless the user specifies otherwise.\nThe user request is: "${userRequest.value}".\nThe list of movies and shows is included below. Only select from this list. Give me a list with IMDb rating, short plot and poster. Use the web.`;
  
  // Add all movies/folders to the list
  filteredAndSortedMovies.value.forEach(movie => {
    const title = movie.title || movie.name || 'Unknown';
    const year = movie.year ? formatYear(movie.year) : '';
    
    // Format as "name, year" or just "name" if year is not available
    if (year) {
      promptText += `${title}, ${year}\n`;
    } else {
      promptText += `${title}\n`;
    }
  });
  
  // Encode the prompt text for URL
  const encodedPrompt = encodeURIComponent(promptText);
  
  // First close the popup to trigger the animation
  showPromptPopup.value = false;
  
  // Use a small timeout to allow the animation to play
  // before opening the new window which could cause focus issues
  setTimeout(() => {
    // Open ChatGPT in a new tab with the prompt
    window.open(`https://chat.openai.com/?temporary-chat=true&q=${encodedPrompt}`, '_blank');
  }, 200); // Adjust timeout to match your animation duration
}

// Backend connection status
const backendConnected = ref(true)
const connectionCheckInterval = ref(null)
const previousConnectionState = ref(true) // Track previous connection state

// Check backend connection status
const checkBackendConnection = async () => {
  try {
    const response = await fetch('http://127.0.0.1:50005/api/health', { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(3000) // 3 second timeout
    })
    
    // Detect reconnection (was disconnected, now connected)
    const wasDisconnected = !previousConnectionState.value
    const nowConnected = response.ok
    
    if (wasDisconnected && nowConnected) {
      // Reconnection detected, reload data
      console.log("Backend reconnected! Reloading data...")
      await reloadData()
    }
    
    // Update connection states
    previousConnectionState.value = backendConnected.value
    backendConnected.value = response.ok
    console.log("Backend connection check:", response.ok ? "Connected" : "Disconnected")
  } catch (error) {
    previousConnectionState.value = backendConnected.value
    backendConnected.value = false
    console.log("Backend connection error:", error)
  }
}

// Add this code to perform an initial check and set up periodic checks
onMounted(async () => {
  // Initial check when component mounts
  await checkBackendConnection()
  
  // Set up periodic checks every 5 seconds
  connectionCheckInterval.value = setInterval(checkBackendConnection, 5000)
})

// Clean up the interval when component unmounts
onUnmounted(() => {
  if (connectionCheckInterval.value) {
    clearInterval(connectionCheckInterval.value)
  }
})

function handleDeleteClick() {
  if (!selectedMovie.value) return;
  const name = selectedMovie.value.title || selectedMovie.value.name;
  if (!window.confirm(`Are you sure you want to delete ${name}?`)) return;
  deleteError.value = '';

  let itemPath = selectedMovie.value.path;
  let itemType = selectedMovie.value.type;

  // If deleting a movie file, check if its parent folder contains only this movie and subtitles
  if (itemType !== "FOLDER" && selectedMovie.value['file-type'] === 'VIDEO') {
    // Find the parent folder in the movies tree
    const parentPath = itemPath.substring(0, itemPath.lastIndexOf('/'));
    // Find the parent folder object in the movies tree
    let parentFolder = null;
    function findFolder(items, targetPath) {
      for (const item of items) {
        if (item.type === 'FOLDER' && item.path === parentPath + '/') {
          return item;
        }
        if (item.children) {
          const found = findFolder(item.children, targetPath);
          if (found) return found;
        }
      }
      return null;
    }
    if (movies.value && Array.isArray(movies.value)) {
      parentFolder = findFolder(movies.value, parentPath + '/');
    }
    if (
      parentFolder &&
      parentFolder.children &&
      parentFolder.children.length > 0 &&
      parentFolder.children.filter(child => child['file-type'] === 'VIDEO').length === 1 &&
      parentFolder.children.every(child => child['file-type'] === 'VIDEO' || child['file-type'] === 'SUBTITLE')
    ) {
      // Only one movie file and the rest are subtitles, delete the folder instead
      itemPath = parentFolder.path;
      itemType = "FOLDER";
    }
  }

  fetch('http://127.0.0.1:50005/api/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: itemPath, type: itemType })
  })
    .then(async response => {
      const result = await response.json();
      if (!response.ok || result.error) {
        deleteError.value = result.error || 'Failed to delete item.';
        return;
      }
      // Refresh items after successful delete
      await reloadData();
      closeInformationContainer();
    })
    .catch(err => {
      deleteError.value = 'Failed to delete item: ' + (err.message || err);
    });
}

// Function to reload data from the backend
const reloadData = async () => {
  try {
    const response = await fetch('http://127.0.0.1:50005/api/movies')
    if (!response.ok) {
      throw new Error(`Failed to fetch movies: ${response.status}`)
    }
    const refreshedMovies = await response.json()
    // Update the movies data
    movies.value = refreshedMovies
    
    // Process the movies data to update UI
    processedMovies.value = refreshedMovies.map(item => processItem(item))
  } catch (error) {
    console.error('Failed to reload data after reconnection:', error)
  }
}


</script>

<style>

</style>
