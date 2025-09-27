export namespace config {
	
	export class Config {
	    serato_db_path: string;
	    music_library_path: string;
	
	    static createFrom(source: any = {}) {
	        return new Config(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.serato_db_path = source["serato_db_path"];
	        this.music_library_path = source["music_library_path"];
	    }
	}

}

